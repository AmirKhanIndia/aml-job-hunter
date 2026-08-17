from workers import WorkerEntrypoint, Response

from scanner import scan_jobs


class Default(WorkerEntrypoint):

    async def fetch(self, request):
        url = str(request.url)

        if url.endswith("/scan"):
            try:
                results = await scan_jobs()

                return Response(
                    f"Scan completed. India eligible jobs: {len(results)}"
                )

            except Exception as error:
                print("SCAN ERROR:", str(error))

                return Response(
                    f"Scan failed: {str(error)}",
                    status=500,
                )

        return Response(
            "AML Job Hunter is online!"
        )

    async def scheduled(self, controller, env, ctx):
        print("========================================")
        print("AML JOB HUNTER CRON STARTED")
        print("========================================")

        try:
            results = await scan_jobs()

            print(
                "Cron scan completed. Eligible jobs:",
                len(results),
            )

        except Exception as error:
            print(
                "CRON ERROR:",
                str(error),
            )

        print("========================================")
        print("AML JOB HUNTER CRON COMPLETED")
        print("========================================")