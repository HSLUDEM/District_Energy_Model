"""Fixed passenger-car demand derived from the 100% electric ETH profiles.

The reference is charging energy, not a measured hourly driving profile. The
first version intentionally assigns all fuels the reference's temporal shape.
Shares are percentages of equivalent vehicle kilometres, not energy shares.
"""
from pathlib import Path

import numpy as np
import pandas as pd


DRIVES = ('petrol', 'diesel', 'bev', 'phev_petrol', 'phev_diesel')


def _positive(parameters, name, allow_zero=False):
    value = parameters[name]
    if (isinstance(value, (bool, str)) or not np.isscalar(value)
            or not np.isfinite(value) or value < 0
            or (value == 0 and not allow_zero)):
        raise ValueError(f'supply.{name} must be finite and '
                         f'{"non-negative" if allow_zero else "positive"}.')
    return float(value)


def validate_shares(shares):
    """Require exactly the supported drives and an explicit 100% total."""
    if not isinstance(shares, dict) or set(shares) != set(DRIVES):
        raise ValueError(f'Mobility shares must contain exactly {DRIVES}.')
    values = {}
    for drive, value in shares.items():
        if (isinstance(value, (bool, str)) or not np.isscalar(value)
                or not np.isfinite(value) or not 0 <= value <= 100):
            raise ValueError(f'Mobility share {drive} must be between 0 and 100.')
        values[drive] = float(value) / 100
    if not np.isclose(sum(values.values()), 1.0, rtol=0, atol=1e-8):
        raise ValueError('Mobility shares must sum to 100 percent.')
    return values


def read_reference_profiles(paths, com_nr, com_percent):
    """Read unchanged municipality CP/PD/PU/FE references, before any scaling."""
    profiles = {}
    for key, filename in (
            ('cp', paths.ev_profile_cp_file), ('pd', paths.ev_profile_pd_file),
            ('pu', paths.ev_profile_pu_file), ('fe', paths.ev_profile_fe_file)):
        frame = pd.read_feather(Path(paths.ev_profiles_dir) / filename)
        if len(com_percent) == 0:
            series = frame[com_nr]
        else:
            missing = com_percent.index.difference(frame.columns)
            if len(missing):
                raise KeyError(f'Municipalities missing from {key.upper()} '
                               f'profile: {missing.tolist()}')
            weights = np.asarray(com_percent, dtype=float)
            if not np.isfinite(weights).all() or (weights < 0).any():
                raise ValueError('Mobility municipality weights must be finite '
                                 'and non-negative.')
            series = frame.loc[:, com_percent.index].mul(com_percent).sum(axis=1)
        values = np.asarray(series, dtype=float)
        if values.ndim != 1 or not np.isfinite(values).all():
            raise ValueError(f'Invalid mobility {key.upper()} profile.')
        profiles[key] = np.maximum(values, 0.0)
    return profiles


class MobilityDemand:
    """Prescribed drive mix. PHEV table values are used directly, unweighted."""

    def __init__(self, profiles, shares_percent, supply, n_hours):
        self.shares = validate_shares(shares_percent)
        if n_hours <= 0 or n_hours % 24:
            raise ValueError('Mobility requires a whole positive number of days.')
        self.profiles = {}
        for key in ('cp', 'pd', 'pu', 'fe'):
            count = n_hours // 24 if key == 'fe' else n_hours
            values = np.asarray(profiles[key], dtype=float)
            if (values.ndim != 1 or len(values) < count
                    or not np.isfinite(values[:count]).all()
                    or (values[:count] < 0).any()):
                raise ValueError(f'Mobility {key} profile must cover {count} '
                                 'finite, non-negative values.')
            self.profiles[key] = values[:count].copy()

        ev = _positive(supply, 'ev_consumption_kWhp100km')
        petrol = _positive(supply, 'petrol_consumption_Lp100km')
        diesel = _positive(supply, 'diesel_consumption_Lp100km')
        phev_p = _positive(supply, 'phev_petrol_consumption_Lp100km')
        phev_d = _positive(supply, 'phev_diesel_consumption_Lp100km')
        phev_pe = _positive(supply, 'phev_petrol_consumption_kWhp100km')
        phev_de = _positive(supply, 'phev_diesel_consumption_kWhp100km')
        self.petrol_kWhpl = (_positive(supply, 'hv_petrol_MJpkg')
                             * _positive(supply, 'density_petrol_kgpl') / 3.6)
        self.diesel_kWhpl = (_positive(supply, 'hv_diesel_MJpkg')
                             * _positive(supply, 'density_diesel_kgpl') / 3.6)
        for fuel in ('petrol', 'diesel'):
            for part in ('combustion', 'upstream'):
                _positive(supply, f'co2_{fuel}_{part}_kgpl', allow_zero=True)

        units_100km = self.profiles['cp'] / ev
        self.km = units_100km * 100
        s = self.shares
        self.petrol_l = units_100km * (s['petrol'] * petrol
                                      + s['phev_petrol'] * phev_p)
        self.diesel_l = units_100km * (s['diesel'] * diesel
                                      + s['phev_diesel'] * phev_d)
        self.phev_electricity = units_100km * (
            s['phev_petrol'] * phev_pe + s['phev_diesel'] * phev_de)
        self.electricity = self.profiles['cp'] * s['bev'] + self.phev_electricity

    def charging_profiles(self):
        """Only BEV load is flexible. PHEV charging stays at its base profile."""
        bev = self.shares['bev']
        return {
            'cp': self.electricity.copy(),
            'pd': self.profiles['pd'] * bev + self.phev_electricity,
            'pu': self.profiles['pu'] * bev + self.phev_electricity,
            'fe': self.profiles['fe'] * bev,
        }

    def reduce_timeframe(self, n_days):
        for name in ('km', 'petrol_l', 'diesel_l', 'phev_electricity', 'electricity'):
            setattr(self, name, getattr(self, name)[:n_days * 24])
        for key in self.profiles:
            count = n_days if key == 'fe' else n_days * 24
            self.profiles[key] = self.profiles[key][:count]

    def update_df_results(self, df, actual_electricity):
        df['d_mobility_km'] = self.km
        df['d_e_mobility_reference'] = self.profiles['cp']
        df['d_e_mobility_phev'] = self.phev_electricity
        df['d_e_mobility_bev'] = np.asarray(actual_electricity) - self.phev_electricity
        for drive, share in self.shares.items():
            df[f'd_mobility_{drive}_km'] = self.km * share
        return df
