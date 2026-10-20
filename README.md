# Trading phone — الليل المالي

Mobile-first protected chart preview. Python standard library only.

Required Railway variables: `APP_PASSWORD` (12+ characters), `ALPACA_API_KEY`, `ALPACA_SECRET_KEY`. The site intentionally requires authentication before exposing data. `APP_PASSWORD` must be configured by the account owner in Railway; never commit secrets.

This first deployment is a safe mobile chart preview, **not** the complete FIRE/liquidity scanner from the Windows build. Historical 15-minute gate, signed trade flow and LIVE FIRE must be migrated separately from V3.4; they are not simulated here.

Alpaca SIP entitlement required for candles. Read-only app.