import requests
import json
import re
from datetime import datetime, timedelta, timezone

def fetch_call_data_by_date(
    url: str = "https://42fd29e5b225.ngrok-free.app/graphql",
    reference_date=None,  # can be None | datetime | "YYYY-MM-DD" | "today"
    days_range: int = 30,
    limit: int = 10
):
    """
    Fetch call transcription data from GraphQL endpoint based on a reference date.

    Args:
        url (str): GraphQL endpoint URL.
        reference_date (datetime, optional): Reference date to calculate date range. 
                                          Defaults to current date if None.
        days_range (int, optional): Number of days to look back from reference_date. 
                                  Defaults to 30.
        limit (int, optional): Limit number of records to return. Defaults to 10.

    Returns:
        list: List of call transcription data dictionaries (limited by `limit`).
    """
    # Normalize reference_date into a timezone-aware UTC datetime.
    # Accepts: None (now), a datetime, or a string like 'today' or 'YYYY-MM-DD' or ISO timestamps.
    def _parse_reference(ref):
        if ref is None:
            return datetime.now(timezone.utc), False
        if isinstance(ref, datetime):
            # make timezone-aware (assume UTC for naive datetimes)
            if ref.tzinfo is None:
                return ref.replace(tzinfo=timezone.utc), False
            return ref.astimezone(timezone.utc), False
        if isinstance(ref, str):
            s = ref.strip()
            if s.lower() in ("today", "now"):
                return datetime.now(timezone.utc), False
            # date-only format YYYY-MM-DD
            if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
                dt = datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                return dt, True
            # try ISO8601 (with or without Z)
            try:
                if s.endswith("Z"):
                    dt = datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
                else:
                    dt = datetime.fromisoformat(s).astimezone(timezone.utc)
                return dt, False
            except Exception:
                raise ValueError(f"Unrecognized date format: {s}")
        raise ValueError("reference_date must be None, datetime, or str in 'YYYY-MM-DD' / ISO format")

    ref_dt, date_only = _parse_reference(reference_date)

    # For date-only inputs, treat the reference as the whole day (00:00 -> 23:59:59.999)
    if date_only:
        start_of_day = ref_dt.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = ref_dt.replace(hour=23, minute=59, second=59, microsecond=999000)
        to_dt = end_of_day
        from_dt = start_of_day - timedelta(days=days_range)
    else:
        to_dt = ref_dt
        from_dt = ref_dt - timedelta(days=days_range)

    # Format as ISO 8601 with Z (milliseconds)
    def _fmt(dt):
        return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    to_date = _fmt(to_dt)
    from_date = _fmt(from_dt)

    # --- GraphQL query ---
    query = f"""
    query GetEntityByHid {{
        getCallDataTranscribe(
            fromDate: "{from_date}"
            toDate: "{to_date}"
        ) {{
            s3Uploaded
            entityId
            callId
            entityName
            state
            phone
            city
            country
            status
            description
            securityDeposit
            minRent
            maxRent
            ownerName
            email
            startedYear
            fullTimeWarden
            visitorsAllowed
            website
            entityType
            totalBeds
            Recordings {{
                s3Url
                dateCreatedInUpdates
            }}
        }}
    }}
    """

    headers = {
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(url, json={"query": query}, headers=headers)

        if response.status_code == 200:
            data = response.json()
            call_data = data.get("data", {}).get("getCallDataTranscribe", [])

            # --- Filter by Recordings.dateCreatedInUpdates (client-side) ---
            filtered = []
            for record in call_data:
                recordings = record.get("Recordings", [])
                matched_recs = []
                for rec in recordings:
                    date_str = rec.get("dateCreatedInUpdates")
                    if not date_str:
                        continue
                    try:
                        rec_dt = datetime.fromisoformat(date_str.replace("Z", "+00:00")).astimezone(timezone.utc)
                    except Exception:
                        # skip invalid date formats
                        continue

                    if rec_dt >= from_dt and rec_dt <= to_dt:
                        matched_recs.append(rec)

                if matched_recs:
                    # include record but only with matching recordings
                    new_record = dict(record)
                    new_record["Recordings"] = matched_recs
                    filtered.append(new_record)

            return filtered[:limit]
        else:
            print(f"❌ Failed! Status code: {response.status_code}")
            print(response.text)
            return []
    except Exception as e:
        print(f"⚠️ Error occurred: {e}")
        return []

# --- Example Usage ---
if __name__ == "__main__":
   
    specific_date = "2025-10-07"
    result = fetch_call_data_by_date(
        reference_date=specific_date # Look back 15 days (will include dates from ~2025-09-21)
    )
    print("\nSpecific date data:")
    print(json.dumps(result, indent=2))