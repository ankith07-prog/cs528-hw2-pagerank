import argparse
import random
import requests

COUNTRIES = [
    "USA", "India", "Canada", "Germany", "France",
    "Brazil", "Japan", "Australia", "Iran", "Cuba"
]

GENDERS = ["Male", "Female"]
INCOMES = ["Low", "Medium", "High"]


def build_headers(rng: random.Random):
    return {
        "X-country": rng.choice(COUNTRIES),
        "X-client-IP": f"192.168.{rng.randint(0,255)}.{rng.randint(1,254)}",
        "X-gender": rng.choice(GENDERS),
        "X-age": str(rng.randint(18, 70)),
        "X-income": rng.choice(INCOMES),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True, help="Base URL like http://34.63.154.245:8080")
    parser.add_argument("--requests", type=int, default=50000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    rng = random.Random(args.seed)

    ok = 0
    not_found = 0
    forbidden = 0
    other = 0
    errors = 0

    for _ in range(args.requests):
        page_num = rng.randint(1, 20000)
        url = f"{args.host}/page_{page_num}.txt"
        headers = build_headers(rng)

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                ok += 1
            elif resp.status_code == 404:
                not_found += 1
            elif resp.status_code == 403:
                forbidden += 1
            else:
                other += 1
        except requests.RequestException:
            errors += 1

    print(f"200={ok}")
    print(f"404={not_found}")
    print(f"403={forbidden}")
    print(f"other={other}")
    print(f"errors={errors}")


if __name__ == "__main__":
    main()
