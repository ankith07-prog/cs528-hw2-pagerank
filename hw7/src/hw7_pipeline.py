import argparse
import logging
import re
from typing import Iterable, List, Tuple

import apache_beam as beam
from apache_beam.io import filesystems
from apache_beam.options.pipeline_options import PipelineOptions


def parse_gcs_file(file_path: str) -> Iterable[Tuple[str, List[str]]]:
    """
    Reads one page file and returns:
    (source_page, [list_of_outgoing_links])

    Example:
        gs://bucket/pages/page_1.txt
    source_page:
        page_1
    """
    source_page = file_path.split("/")[-1].replace(".txt", "")

    with filesystems.FileSystems.open(file_path) as f:
        content = f.read().decode("utf-8")

    links = [line.strip() for line in content.splitlines() if line.strip()]
    yield (source_page, links)


def format_kv(item: Tuple[str, int]) -> str:
    key, value = item
    return f"{key}\t{value}"


def extract_incoming_pairs(page_data: Tuple[str, List[str]]) -> Iterable[Tuple[str, int]]:
    """
    For each outgoing link from a source page, emit:
        (target_page, 1)
    """
    _, links = page_data
    for target in links:
        yield (target, 1)


def extract_outgoing_counts(page_data: Tuple[str, List[str]]) -> Tuple[str, int]:
    """
    Emit:
        (source_page, number_of_outgoing_links)
    """
    source_page, links = page_data
    return (source_page, len(links))


def extract_bigrams(page_data: Tuple[str, List[str]]) -> Iterable[Tuple[str, int]]:
    """
    Since each file contains page IDs line by line, compute consecutive
    page-ID bigrams within each file.

    Example lines:
        page_5
        page_7
        page_9

    Bigrams:
        "page_5 page_7"
        "page_7 page_9"
    """
    _, links = page_data
    for i in range(len(links) - 1):
        bigram = f"{links[i]} {links[i + 1]}"
        yield (bigram, 1)


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        required=True,
        help="Input file pattern, e.g. gs://bucket/pages/*.txt",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output base path, e.g. gs://bucket/hw7-output or ./output",
    )

    known_args, pipeline_args = parser.parse_known_args(argv)
    pipeline_options = PipelineOptions(pipeline_args)

    with beam.Pipeline(options=pipeline_options) as p:
        page_data = (
            p
            | "MatchFiles" >> beam.Create(filesystems.FileSystems.match([known_args.input])[0].metadata_list)
            | "GetFilePaths" >> beam.Map(lambda metadata: metadata.path)
            | "ReadEachFile" >> beam.FlatMap(parse_gcs_file)
        )

        # Top 5 outgoing links
        outgoing_top5 = (
            page_data
            | "OutgoingCounts" >> beam.Map(extract_outgoing_counts)
            | "Top5Outgoing" >> beam.combiners.Top.Of(5, key=lambda kv: kv[1])
            | "FlattenOutgoingTop5" >> beam.FlatMap(lambda x: x)
            | "FormatOutgoing" >> beam.Map(format_kv)
        )

        outgoing_top5 | "WriteOutgoingTop5" >> beam.io.WriteToText(
            f"{known_args.output}/outgoing_top5/result",
            shard_name_template=""
        )

        # Top 5 incoming links
        incoming_top5 = (
            page_data
            | "IncomingPairs" >> beam.FlatMap(extract_incoming_pairs)
            | "SumIncomingCounts" >> beam.CombinePerKey(sum)
            | "Top5Incoming" >> beam.combiners.Top.Of(5, key=lambda kv: kv[1])
            | "FlattenIncomingTop5" >> beam.FlatMap(lambda x: x)
            | "FormatIncoming" >> beam.Map(format_kv)
        )

        incoming_top5 | "WriteIncomingTop5" >> beam.io.WriteToText(
            f"{known_args.output}/incoming_top5/result",
            shard_name_template=""
        )

        # Top 5 bigrams
        bigram_top5 = (
            page_data
            | "BigramPairs" >> beam.FlatMap(extract_bigrams)
            | "SumBigramCounts" >> beam.CombinePerKey(sum)
            | "Top5Bigrams" >> beam.combiners.Top.Of(5, key=lambda kv: kv[1])
            | "FlattenBigramTop5" >> beam.FlatMap(lambda x: x)
            | "FormatBigrams" >> beam.Map(format_kv)
        )

        bigram_top5 | "WriteBigramTop5" >> beam.io.WriteToText(
            f"{known_args.output}/bigrams_top5/result",
            shard_name_template=""
        )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    run()