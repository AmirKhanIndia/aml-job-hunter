from urllib.parse import urlparse
import json
import traceback

from workers import WorkerEntrypoint, Response, fetch

from scanner import scan_jobs


class Default(WorkerEntrypoint):

    async def fetch(self, request):
        url = urlparse(request.url)

        # --------------------------------------------------
        # BASIC HEALTH CHECK
        # --------------------------------------------------

        if url.path == "/":
            return Response(
                "AML Job Hunter is online!"
            )

        # --------------------------------------------------
        # TELEGRAM TEST
        # --------------------------------------------------

        if url.path == "/telegram-test":
            try:
                return await self.telegram_test()

            except Exception as error:
                print(
                    "TELEGRAM TEST ERROR:",
                    repr(error),
                )

                print(
                    traceback.format_exc()
                )

                return Response(
                    "Telegram test exception: "
                    + repr(error),
                    status=500,
                )

        # --------------------------------------------------
        # MANUAL SCAN
        # --------------------------------------------------

        if url.path == "/scan":

            try:
                print(
                    "========================================"
                )

                print(
                    "MANUAL SCAN REQUEST RECEIVED"
                )

                print(
                    "========================================"
                )

                results = await scan_jobs()

                print(
                    "SCAN SUCCESS"
                )

                print(
                    "Eligible jobs:",
                    len(results),
                )

                return Response(
                    "Scan completed. India eligible jobs: "
                    + str(len(results))
                )

            except Exception as error:

                error_message = repr(error)

                error_trace = traceback.format_exc()

                print(
                    "========================================"
                )

                print(
                    "SCAN ERROR"
                )

                print(
                    "Exception:",
                    error_message,
                )

                print(
                    error_trace
                )

                print(
                    "========================================"
                )

                return Response(
                    "SCAN EXCEPTION\n\n"
                    + error_message
                    + "\n\nTRACEBACK:\n"
                    + error_trace,
                    status=500,
                )

        # --------------------------------------------------
        # UNKNOWN ROUTE
        # --------------------------------------------------

        return Response(
            "AML Job Hunter is online!"
        )

    # ======================================================
    # TELEGRAM TEST
    # ======================================================

    async def telegram_test(self):

        token = self.env.TELEGRAM_BOT_TOKEN

        if not token:
            return Response(
                "TELEGRAM_BOT_TOKEN is missing",
                status=500,
            )

        # --------------------------------------------------
        # GET TELEGRAM UPDATES
        # --------------------------------------------------

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
                "Telegram getUpdates failed\n\n"
                + error_text,
                status=500,
            )

        data = await updates_response.json()

        updates = data.get(
            "result",
            [],
        )

        if not updates:

            return Response(
                "No Telegram message found. "
                "Open the bot and send /start first."
            )

        # --------------------------------------------------
        # FIND CHAT ID
        # --------------------------------------------------

        chat_id = None

        for update in reversed(updates):

            message = update.get(
                "message"
            )

            if not message:
                continue

            chat = message.get(
                "chat"
            )

            if not chat:
                continue

            chat_id = chat.get(
                "id"
            )

            if chat_id is not None:
                break

        if chat_id is None:

            return Response(
                "Could not find Telegram chat ID.",
                status=500,
            )

        # --------------------------------------------------
        # SEND TEST MESSAGE
        # --------------------------------------------------

        send_url = (
            f"https://api.telegram.org/bot{token}/sendMessage"
        )

        payload = {
            "chat_id": chat_id,
            "text": (
                "AML Job Hunter connected!\n\n"
                "Cloudflare Worker -> Telegram is working.\n\n"
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
                "Telegram sendMessage failed\n\n"
                + error_text,
                status=500,
            )

        return Response(
            "Telegram test message sent successfully!"
        )

    # ======================================================
    # CRON
    # ======================================================

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
                "Cron scan completed."
            )

            print(
                "Eligible jobs:",
                len(results),
            )

        except Exception as error:

            print(
                "========================================"
            )

            print(
                "CRON ERROR:",
                repr(error),
            )

            print(
                traceback.format_exc()
            )

            print(
                "========================================"
            )

        print(
            "AML JOB HUNTER CRON COMPLETED"
        )