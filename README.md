# Amul Stock Checker → Email Alert

Checks the Amul Whey Protein (60 sachets) product for pincode **560016** every
4 hours, and emails you the moment it's back in stock.

- Product: https://shop.amul.com/en/product/amul-whey-protein-32-g-or-pack-of-60-sachets
- Pincode: 560016
- Runs on: GitHub Actions (free) — no need to keep your own PC on
- Notifies via: Gmail SMTP

---

## 1. Create a Gmail App Password (so the bot can send mail as you)

1. Go to your Google Account → Security → make sure **2-Step Verification** is ON
   (App Passwords require it). Direct link: https://myaccount.google.com/security
2. Go to https://myaccount.google.com/apppasswords
3. Create a new app password (name it e.g. "Amul Stock Bot")
4. Google gives you a 16-character password like `abcd efgh ijkl mnop` — copy it
   (remove spaces). This is **not** your normal Gmail password — keep it secret.

## 2. Create a GitHub repository

1. Go to https://github.com/new, create a new **private** repository
   (e.g. `amul-stock-bot`)
2. Upload these files, keeping the folder structure exactly as-is:
   ```
   amul-stock-bot/
   ├── check_stock.py
   ├── requirements.txt
   └── .github/
       └── workflows/
           └── check-stock.yml
   ```
   Easiest way: on the repo page, click "Add file" → "Upload files" and drag
   the whole folder in (GitHub preserves folder paths on upload).

## 3. Add your secrets (so credentials never appear in code)

In your new repo: **Settings → Secrets and variables → Actions → New repository secret**

Add three secrets:

| Secret name           | Value                                      |
|------------------------|---------------------------------------------|
| `GMAIL_USER`           | `dhanushspjimr@gmail.com`                  |
| `GMAIL_APP_PASSWORD`   | the 16-character app password from step 1  |
| `TO_EMAIL`             | `dhanushspjimr@gmail.com` (or any address you want alerts sent to) |

## 4. Test it manually first

1. Go to the **Actions** tab in your repo
2. Click **Check Amul Stock** on the left → **Run workflow** → **Run workflow**
3. Wait ~30–60 seconds, then click into the run to see the logs
4. You should see log lines like:
   ```
   Checking: https://shop.amul.com/...
   Result: out of stock
   ```
5. If it says `IN STOCK`, check your inbox — you should get the email.

If the script can't find the pincode box or stock status (logged as a
warning), download the **debug-output** artifact from that run (screenshots +
page HTML) — that'll show exactly what the page looked like, and I can help
you adjust the selectors in `check_stock.py`.

## 5. Let it run automatically

Once the manual test works, you're done — the workflow in
`.github/workflows/check-stock.yml` is already scheduled to run **every 4
hours automatically**. No further action needed.

You can change the schedule by editing the `cron` line in that file
(cron times are in UTC).

## 6. To track a different product or pincode later

Edit the `PRODUCT_URL` and `PINCODE` values in
`.github/workflows/check-stock.yml` under `env:`, commit the change, and the
next scheduled (or manual) run will use the new values.

---

### Notes & limitations

- This is an **unofficial** automation that interacts with the public Amul
  shopping site the same way a browser would — it isn't using any private
  or hidden API. Use responsibly and don't reduce the check interval too
  aggressively (every 4 hours is reasonable).
- Amul's site occasionally tweaks its page layout, which could break the
  pincode-selection or stock-detection logic. The debug artifacts (screenshot
  + HTML) make it quick to fix if that happens — just share them with me.
- GitHub Actions free tier includes 2,000 minutes/month for private repos,
  which is more than enough for a check every 4 hours (~6 runs/day, each
  taking under a minute).
