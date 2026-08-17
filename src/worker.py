from workers import WorkerEntrypoint, Response

from scanner import scan_jobs


class Default(WorkerEntrypoint):

    async def fetch(self, request):
        return Response(
            "AML Job Hunter is online!"
        )

    async def scheduled(
        self,
        controller,
        env,
        ctx,
    ):
        print(
            "========================================"
        )
        print(
            "AML JOB HUNTER CRON STARTED"
        )
        print(
            "========================================"
        )

        try:

            results = await scan_jobs()

            print(
                "Cron scan finished."
            )

            print(
                "Eligible jobs:",
                len(results),
            )

        except Exception as error:

            print(
                "CRON ERROR:",
                str(error),
            )

        print(
            "========================================"
        )
        print(
            "AML JOB HUNTER CRON COMPLETED"
        )
        print(
            "========================================"
        )