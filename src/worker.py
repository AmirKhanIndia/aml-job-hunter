from urllib.parse import urlparse
import json

from workers import WorkerEntrypoint, Response, fetch

from scanner import scan_jobs


class Default(WorkerEntrypoint):

    async def fetch(self, request):
        url = urlparse(request.url)

        if url.path == "/telegram-test":
            return await self.telegram_test()

        if url.path == "/scan":
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

    async def telegram_test(self):

        token = self.env.TELEGRAM_BOT_TOKEN

        if not token:
            return Response(
                "TELEGRAM_BOT_TOKEN is missing",
                status=500,
            )

        updates_url = (
            f"https://api.telegram.org/bot{token}/getUpdates"
        )

        updates_response = await fetch(
            updates_url,
            method="GET",
        )

        if updates_response.status != 200:
            error_text = await updates_response.text()

            print(
                "Telegram getUpdates error:",
                error_text,
            )

            return Response(
                "Telegram getUpdates failed",
                status=500,
            )

        data = await updates_response.json()

        updates = data.get("result", [])

        if not updates:
            return Response(
                "No Telegram message found. Open the bot and send /start first."
            )

        chat_id = None

        for update in reversed(updates):

            message = update.get("message")

            if not message:
                continue

            chat = message.get("chat")

            if not chat:
                continue

            chat_id = chat.get("id")

            if chat_id is not None:
                break

        if chat_id is None:
            return Response(
                "Could not find Telegram chat ID.",
                status=500,
            )

        send_url = (
            f"https://api.telegram.org/bot{token}/sendMessage"
        )

        payload = {
            "chat_id": chat_id,
            "text": (
                "🚀 AML Job Hunter connected!\n\n"
                "Cloudflare Worker → Telegram is working.\n\n"
                "Next step: automatic job alerts."
            ),
        }

        send_response = await fetch(
            send_url,
            method="POST",
            headers={
                "Content-Type": "application/json",
            },
            body=json.dumps(payload),
        )

        if send_response.status != 200:

            error_text = await send_response.text()

            print(
                "Telegram sendMessage error:",
                error_text,
            )

            return Response(
                "Telegram sendMessage failed",
                status=500,
            )

        return Response(
            "Telegram test message sent successfully!"
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

        print(
            "AML JOB HUNTER CRON COMPLETED"
        )