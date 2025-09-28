import requests
import datetime

def check_endpoint(url, method='get', headers=None, json=None, dry_run=False):
    try:
        if dry_run:
            print(f"[DRY RUN] Would send a {method.upper()} request to {url}")
            return 200, 0, "Dry run successful"

        start_time = datetime.datetime.now()
        if method == 'get':
            response = requests.get(url, headers=headers, timeout=10)
        elif method == 'post':
            response = requests.post(url, headers=headers, json=json, timeout=10)
        end_time = datetime.datetime.now()

        latency = (end_time - start_time).total_seconds() * 1000
        return response.status_code, latency, response.text
    except requests.exceptions.RequestException as e:
        return -1, -1, str(e)

if __name__ == "__main__":
    # 探測 /health
    status, latency, content = check_endpoint("http://localhost:8000/health")
    print(f"/health: Status={status}, Latency={latency:.2f}ms")

    # 探測 /healthz
    status, latency, content = check_endpoint("http://localhost:8000/healthz")
    print(f"/healthz: Status={status}, Latency={latency:.2f}ms")

    # 探測 /auth/register (dry-run/mock)
    status, latency, content = check_endpoint("http://localhost:8000/auth/register", method='post', json={}, dry_run=True)
    print(f"/auth/register (dry-run): Status={status}, Latency={latency:.2f}ms")

    # 探測 /referral/stats (auth)
    # 這部分需要一個有效的認證令牌
    # 在實際使用中，您需要替換 'YOUR_AUTH_TOKEN'
    headers = {"Authorization": "Bearer YOUR_AUTH_TOKEN"}
    status, latency, content = check_endpoint("http://localhost:8000/referral/stats", headers=headers)
    print(f"/referral/stats: Status={status}, Latency={latency:.2f}ms")


