from workers import WorkerEntrypoint, Response


class Default(WorkerEntrypoint):

    async def fetch(self, request):
        return Response("AML Job Hunter is online!")

    async def scheduled(self, controller, env, ctx):
        print("AML Job Hunter scheduled scan started")

        # Job scanner yahan connect hoga
        # Abhi sirf test run hai

        print("AML Job Hunter scheduled scan completed")