import argparse
import logging
from typing import Iterable, List, Tuple

import apache_beam as beam
from apache_beam.io import fileio
from apache_beam.options.pipeline_options import PipelineOptions


def parse_readable_file(readable_file) -> Iterable[Tuple[str, List[str]]]:
    """
    Read one file and return:
    (source_page, [outgoing links])
    """
    file_path = readable_file.metadata.path
    source_page = file_path.split("/")[-1].replace(".txt", "")

    content = readable_file.read_utf8()
    links = [line.strip() for line in content.splitlines() if line.strip()]
    yield (source_page, links)


def extract_outgoing(page_data: Tuple[str, List[str]]) -> Tuple[str, int]:
    source_page, links = page_data
    return (source_page, len(links))


def extract_incoming(page_data: Tuple[str, List[str]]) -> Iterable[Tuple[str, int]]:
    _, links = page_data
    for link in links:
        yield (link, 1)


def extract_bigrams(page_data: Tuple[str, List[str]]) -> Iterable[Tuple[str, int]]:
    _, links = page_data
    for i in range(len(links) - 1):
        yield (f"{links[i]} {links[i + 1]}", 1)


def format_result(item: Tuple[str, int]) -> str:
    key, value = item
    return f"{key}\t{value}"


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        required=True,
        help="Input pattern, for example gs://bucket/pages/*.txt",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output path, for example ./hw7/output/local or gs://bucket/hw7-output",
    )

    known_args, pipeline_args = parser.parse_known_args(argv)
    pipeline_options = PipelineOptions(pipeline_args)

    with beam.Pipeline(options=pipeline_options) as pipeline:
        page_data = (
            pipeline
            | "MatchFiles" >> fileio.MatchFiles(known_args.input)
            | "ReadMatches" >> fileio.ReadMatches()
            | "ParseFiles" >> beam.FlatMap(parse_readable_file)
        )

        outgoing_top5 = (
            page_data
            | "OutgoingCounts" >> beam.Map(extract_outgoing)
            | "Top5Outgoing" >> beam.combiners.Top.Of(5, key=lambda kv: kv[1])
            | "FlattenOutgoing" >> beam.FlatMap(lambda rows: rows)
            | "FormatOutgoing" >> beam.Map(format_result)
        )

        incoming_top5 = (
            page_data
            | "IncomingPairs" >> beam.FlatMap(extract_incoming)
            | "CountIncoming" >> beam.CombinePerKey(sum)
            | "Top5Incoming" >> beam.combiners.Top.Of(5, key=lambda kv: kv[1])
            | "FlattenIncoming" >> beam.FlatMap(lambda rows: rows)
            | "FormatIncoming" >> beam.Map(format_result)
        )

        bigrams_top5 = (
            page_data
            | "BigramPairs" >> beam.FlatMap(extract_bigrams)
            | "CountBigrams" >> beam.CombinePerKey(sum)
            | "Top5Bigrams" >> beam.combiners.Top.Of(5, key=lambda kv: kv[1])
            | "FlattenBigrams" >> beam.FlatMap(lambda rows: rows)
            | "FormatBigrams" >> beam.Map(format_result)
        )

        outgoing_top5 | "WriteOutgoing" >> beam.io.WriteToText(
            f"{known_args.output}/outgoing_top5/result",
            shard_name_template=""
        )

        incoming_top5 | "WriteIncoming" >> beam.io.WriteToText(
            f"{known_args.output}/incoming_top5/result",
            shard_name_template=""
        )

        bigrams_top5 | "WriteBigrams" >> beam.io.WriteToText(
            f"{known_args.output}/bigrams_top5/result",
            shard_name_template=""
        )


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    run()