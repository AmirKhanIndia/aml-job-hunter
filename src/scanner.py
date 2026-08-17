import asyncio

from scanner import scan_jobs


async def main():
    print()
    print("========================================")
    print("          AML / KYC JOB HUNTER")
    print("========================================")

    try:
        results = await scan_jobs()

        print()
        print("========================================")
        print("             FINAL RESULTS")
        print("========================================")

        print(
            "India eligible jobs:",
            len(results),
        )

        print()
        print("Scanner execution completed.")

    except Exception as error:
        print()
        print("========================================")
        print("              SCAN ERROR")
        print("========================================")

        print(
            type(error).__name__ + ":",
            str(error),
        )


if __name__ == "__main__":
    asyncio.run(main())