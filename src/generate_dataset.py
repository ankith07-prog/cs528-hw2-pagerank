import os
import random

NUM_FILES = 20000
MAX_LINKS = 375
OUT_DIR = "pages"

random.seed(42)
os.makedirs(OUT_DIR, exist_ok=True)

pages = [f"page_{i}" for i in range(NUM_FILES)]

for page in pages:
    num_links = random.randint(0, MAX_LINKS)
    links = random.sample(pages, min(num_links, NUM_FILES)) if num_links > 0 else []

    with open(os.path.join(OUT_DIR, f"{page}.txt"), "w") as f:
        for link in links:
            f.write(link + "\n")

print("Dataset generated.")
