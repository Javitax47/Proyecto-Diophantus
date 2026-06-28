"""
================================================================================
   DIOPHANTUS PRODUCT - MEDICIÓN DE USO Y TIERS  (pricing enforzable, C1/§4)
================================================================================
Primitiva mínima para que el pricing del plan (Hobby/Pro/Team + uso por
verificación) sea ENFORZABLE en el SaaS, no sólo una tabla en un documento:
cuotas por tier, conteo de uso persistente y decisión allow/deny + coste por
verificación extra. Es el gancho de facturación; el cobro real (Stripe, etc.)
se conecta encima.

Tiers (alineados con MONETIZACION.md §4):
  hobby : gratis, cuota mensual limitada.
  pro   : $99/mes, cuota amplia, $0.50 por verificación extra.
  team  : $999/mes, cuota muy amplia, $0.30 por verificación extra.
"""

import os
import json
import datetime

TIERS = {
    'hobby': {'price_usd_month': 0,   'monthly_quota': 50,    'overage_usd': None},
    'pro':   {'price_usd_month': 99,  'monthly_quota': 5000,  'overage_usd': 0.50},
    'team':  {'price_usd_month': 999, 'monthly_quota': 100000, 'overage_usd': 0.30},
}


def _period(now=None):
    now = now or datetime.datetime.now(datetime.timezone.utc)
    return f"{now.year:04d}-{now.month:02d}"


class UsageMeter:
    """Medidor de uso persistente (JSON). Cuenta verificaciones por cuenta y
    periodo y decide si una verificación está permitida según el tier."""

    def __init__(self, store_path):
        self.path = store_path
        self.data = {}
        if os.path.exists(store_path):
            with open(store_path, encoding="utf-8") as f:
                self.data = json.load(f)

    def _save(self):
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)

    def used(self, account, period=None):
        period = period or _period()
        return self.data.get(account, {}).get(period, 0)

    def authorize(self, account, tier, period=None):
        """Decide si se permite una verificación. Devuelve dict con allowed,
        within_quota, overage_usd (coste si excede cuota), used, quota."""
        if tier not in TIERS:
            raise ValueError(f"tier desconocido: {tier}")
        period = period or _period()
        quota = TIERS[tier]['monthly_quota']
        overage = TIERS[tier]['overage_usd']
        used = self.used(account, period)
        within = used < quota
        allowed = within or (overage is not None)
        return {
            'allowed': allowed, 'within_quota': within,
            'overage_usd': 0.0 if within else (overage or 0.0),
            'used': used, 'quota': quota, 'tier': tier, 'period': period,
        }

    def record(self, account, period=None):
        """Registra una verificación consumida (tras autorizar)."""
        period = period or _period()
        self.data.setdefault(account, {})
        self.data[account][period] = self.data[account].get(period, 0) + 1
        self._save()
        return self.data[account][period]


def price_quote(tier, verifications_per_month):
    """Estimación de factura mensual para un volumen dado (para la web de pricing)."""
    if tier not in TIERS:
        raise ValueError(tier)
    t = TIERS[tier]
    base = t['price_usd_month']
    extra = max(0, verifications_per_month - t['monthly_quota'])
    over = (t['overage_usd'] or 0.0) * extra
    return {'tier': tier, 'base_usd': base, 'overage_usd': round(over, 2),
            'total_usd': round(base + over, 2), 'verifications': verifications_per_month}
