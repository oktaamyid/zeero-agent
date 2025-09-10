# zeero-agent

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 6969
```


## Test
```bash
curl -s -X POST https://supreme-spork-6p9q4grq54vhxrv4-6969.app.github.dev/v1/chat \
-H 'Content-Type: application/json' \
-d '{"query":"Apa jadwal ORMIK?"}' | jq
```


## Next.js fetch example
```ts
// app/api/zeero/route.ts (Next.js 14 App Router)
import { NextRequest, NextResponse } from 'next/server'


export async function POST(req: NextRequest) {
    const { query } = await req.json()
    const res = await fetch(process.env.ZEERO_API_URL + '/v1/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
})

const data = await res.json()
    return NextResponse.json(data)
}
```


## Response shape
```json
{
"answer": "...markdown...",
"confidence": 0.8,
"topic_ok": true,
"truncated": false
}