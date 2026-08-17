from urllib.parse import urlparse
import json
import traceback

from workers import WorkerEntrypoint, Response, fetch

from scanner import scan_jobs


MAX_TELEGRAM_ALERTS_PER_SCAN = 10


class Default(WorkerEntrypoint):

    async def fetch(self, request):
        url = urlparse(request.url)

        if url.path == "/":
            return Response(
                "AML Job Hunter is online!"
            )

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

        if url.path == "/scan":
            try:
                print(
                    "========================================"
                )

                print(
                    "MANUAL SCAN STARTED"
                )

                results = await scan_jobs()

                print(
                    "Eligible jobs:",
                    len(results),
                )

                telegram_result = await self.send_job_alerts(
                    results
                )

                return Response(
                    "Scan completed.\n"
                    "India eligible jobs: "
                    + str(len(results))
                    + "\n"
                    "Telegram alerts sent: "
                    + str(telegram_result["sent"])
                    + "\n"
                    "Skipped duplicates: "
                    + str(telegram_result["duplicates"])
                )

            except Exception as error:
                print(
                    "SCAN ERROR:",
                    repr(error),
                )

                print(
                    traceback.format_exc()
                )

                return Response(
                    "SCAN EXCEPTION\n\n"
                    + repr(error)
                    + "\n\nTRACEBACK:\n"
                    + traceback.format_exc(),
                    status=500,
                )

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

        updates_url = (
            f"https://api.telegram.org/bot{token}/getUpdates"
        )

        updates_response = await fetch(
            updates_url,
            method="GET",
        )

        if updates_response.status != 200:

            error_text = await updates_response.text()

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

        chat_id = self.find_chat_id(
            updates
        )

        if chat_id is None:
            return Response(
                "Could not find Telegram chat ID.",
                status=500,
            )

        success = await self.send_telegram_message(
            token,
            chat_id,
            (
                "AML Job Hunter connected!\n\n"
                "Cloudflare Worker -> Telegram is working.\n\n"
                "Automatic job alerts are ready."
            ),
        )

        if not success:
            return Response(
                "Telegram sendMessage failed",
                status=500,
            )

        return Response(
            "Telegram test message sent successfully!"
        )

    # ======================================================
    # FIND TELEGRAM CHAT
    # ======================================================

    def find_chat_id(self, updates):

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
                return chat_id

        return None

    # ======================================================
    # SEND TELEGRAM MESSAGE
    # ======================================================

    async def send_telegram_message(
        self,
        token,
        chat_id,
        text,
    ):

        send_url = (
            f"https://api.telegram.org/bot{token}/sendMessage"
        )

        payload = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": False,
        }

        response = await fetch(
            send_url,
            method="POST",
            headers={
                "Content-Type": "application/json",
            },
            body=json.dumps(payload),
        )

        if response.status != 200:

            error_text = await response.text()

            print(
                "Telegram sendMessage error:",
                error_text,
            )

            return False

        return True

    # ======================================================
    # CREATE JOB MESSAGE
    # ======================================================

    def format_job_message(self, result):

        job = result["job"]

        company = job.get(
            "_company",
            "Unknown",
        )

        title = job.get(
            "title",
            "Unknown role",
        )

        location = job.get(
            "location",
            "",
        )

        if isinstance(location, dict):
            location = location.get(
                "name",
                "",
            )

        url = job.get(
            "absolute_url",
            "",
        )

        score = result.get(
            "score",
            0,
        )

        roles = result.get(
            "matched_roles",
            [],
        )

        skills = result.get(
            "matched_skills",
            [],
        )

        experience = result.get(
            "experience_matches",
            [],
        )

        role_text = (
            ", ".join(roles)
            if roles
            else "AML/KYC"
        )

        skills_text = (
            ", ".join(skills[:8])
            if skills
            else "None"
        )

        experience_text = (
            ", ".join(experience[:8])
            if experience
            else "None"
        )

        message = (
            "AML JOB MATCH\n\n"
            f"Company: {company}\n"
            f"Role: {title}\n"
            f"Location: {location}\n\n"
            f"Match Score: {score}/100\n"
            f"Category: {role_text}\n\n"
            f"Matched Skills:\n"
            f"{skills_text}\n\n"
            f"Relevant Experience:\n"
            f"{experience_text}\n\n"
            f"Apply:\n{url}"
        )

        return message

    # ======================================================
    # UNIQUE JOB ID
    # ======================================================

    def get_job_id(self, result):

        job = result["job"]

        absolute_url = job.get(
            "absolute_url",
            "",
        )

        if absolute_url:
            return absolute_url

        job_id = job.get(
            "id"
        )

        if job_id is not None:
            return (
                str(job.get("_company", ""))
                + ":"
                + str(job_id)
            )

        company = job.get(
            "_company",
            "",
        )

        title = job.get(
            "title",
            "",
        )

        return (
            company
            + "|"
            + title
        )

    # ======================================================
    # KV DUPLICATE CHECK
    # ======================================================

    async def job_was_seen(self, job_id):

        key = "job:" + job_id

        try:
            value = await self.env.SEEN_JOBS.get(
                key
            )

            return value is not None

        except Exception as error:

            print(
                "KV GET ERROR:",
                repr(error),
            )

            raise

    # ======================================================
    # MARK JOB AS SEEN
    # ======================================================

    async def mark_job_seen(self, job_id):

        key = "job:" + job_id

        try:
            await self.env.SEEN_JOBS.put(
                key,
                "seen",
            )

        except Exception as error:

            print(
                "KV PUT ERROR:",
                repr(error),
            )

            raise

    # ======================================================
    # SEND JOB ALERTS
    # ======================================================

    async def send_job_alerts(
        self,
        results,
    ):

        token = self.env.TELEGRAM_BOT_TOKEN

        if not token:
            raise Exception(
                "TELEGRAM_BOT_TOKEN is missing"
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

            raise Exception(
                "Telegram getUpdates failed: "
                + error_text
            )

        data = await updates_response.json()

        updates = data.get(
            "result",
            [],
        )

        if not updates:
            raise Exception(
                "No Telegram chat found. "
                "Send /start to the bot first."
            )

        chat_id = self.find_chat_id(
            updates
        )

        if chat_id is None:
            raise Exception(
                "Could not find Telegram chat ID."
            )

        sent = 0
        duplicates = 0

        sorted_results = sorted(
            results,
            key=lambda item: item.get(
                "score",
                0,
            ),
            reverse=True,
        )

        for result in sorted_results:

            job_id = self.get_job_id(
                result
            )

            # Check persistent KV
            already_seen = await self.job_was_seen(
                job_id
            )

            if already_seen:

                duplicates += 1

                print(
                    "Duplicate skipped:",
                    job_id,
                )

                continue

            if sent >= MAX_TELEGRAM_ALERTS_PER_SCAN:
                break

            message = self.format_job_message(
                result
            )

            success = await self.send_telegram_message(
                token,
                chat_id,
                message,
            )

            if not success:
                continue

            # Only mark as seen AFTER Telegram succeeds
            await self.mark_job_seen(
                job_id
            )

            sent += 1

            print(
                "Telegram alert sent:",
                job_id,
            )

        print(
            "Telegram alerts sent:",
            sent,
        )

        print(
            "Duplicate jobs skipped:",
            duplicates,
        )

        return {
            "sent": sent,
            "duplicates": duplicates,
        }

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

        try:

            results = await scan_jobs()

            print(
                "Cron scan completed."
            )

            print(
                "Eligible jobs:",
                len(results),
            )

            telegram_result = await self.send_job_alerts(
                results
            )

            print(
                "Telegram alerts sent:",
                telegram_result["sent"],
            )

            print(
                "Duplicate jobs skipped:",
                telegram_result["duplicates"],
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