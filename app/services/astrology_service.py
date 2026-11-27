from datetime import datetime, timedelta, timezone
try:
    import swisseph as swe
except ImportError:
    swe = None
from fastapi import HTTPException
from app.schemas.astrology import AstrologyChartRequest
from app.utils.i18n import localize_chart, validate_language

SIGNS = ("Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces")
NAKSHATRAS = ("Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati")
PLANET_CODES = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu")
DASHA_LORDS = ("Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury")
DASHA_YEARS = (7, 20, 6, 10, 7, 18, 16, 19, 17)

def sign_name(longitude: float) -> str:
    return SIGNS[int(longitude // 30) % 12]

def _planet_position(jd: float, planet: int, flags: int) -> float:
    result, _ = swe.calc_ut(jd, planet, flags)
    return result[0] % 360

def _house_for(longitude: float, cusps) -> int:
    for index in range(12):
        start = float(cusps[index]) % 360
        end = float(cusps[(index + 1) % 12]) % 360
        span = (end - start) % 360
        if (longitude - start) % 360 < span:
            return index + 1
    return 12

def _navamsa(longitude: float) -> str:
    sign = int(longitude // 30) % 12
    part = int((longitude % 30) / (30 / 9))
    modality_start = sign if sign % 3 == 0 else ((sign + 8) % 12 if sign % 3 == 1 else (sign + 4) % 12)
    return SIGNS[(modality_start + part) % 12]

async def generate_chart(request: AstrologyChartRequest, language: str = "en") -> dict:
    """Calculate a Lahiri sidereal chart with Swiss Ephemeris. Coordinates are required."""
    language = validate_language(language)
    if swe is None:
        raise HTTPException(503, "Swiss Ephemeris is not installed. Install requirements-astrology.txt in the active environment.")
    try:
        swe.set_sid_mode(swe.SIDM_LAHIRI)
        dt = request.birth_datetime.astimezone(timezone.utc)
        hour = dt.hour + dt.minute / 60 + dt.second / 3600 + dt.microsecond / 3_600_000_000
        jd = swe.julday(dt.year, dt.month, dt.day, hour)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
        cusps, angles = swe.houses_ex(jd, request.latitude, request.longitude, request.house_system.encode(), swe.FLG_SIDEREAL)
        ascendant = angles[0] % 360
        planets = []
        planet_codes = {"Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY, "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE}
        for name in PLANET_CODES:
            code = planet_codes[name]
            longitude = _planet_position(jd, code, flags)
            house = _house_for(longitude, cusps)
            planets.append({"name": name, "longitude": round(longitude, 6), "rasi": sign_name(longitude),
                            "navamsa": _navamsa(longitude), "house": house})
        rahu = next(p for p in planets if p["name"] == "Rahu")
        ketu_longitude = (rahu["longitude"] + 180) % 360
        planets.append({"name": "Ketu", "longitude": round(ketu_longitude, 6), "rasi": sign_name(ketu_longitude),
                        "navamsa": _navamsa(ketu_longitude), "house": _house_for(ketu_longitude, cusps)})
        moon = next(p for p in planets if p["name"] == "Moon")
        nak_index = int(moon["longitude"] / (360 / 27))
        within_nak = (moon["longitude"] % (360 / 27)) / (360 / 27)
        lord_index = nak_index % 9
        balance = DASHA_YEARS[lord_index] * (1 - within_nak)
        dasha_year_days = 365.25
        elapsed_mahadasha_days = (DASHA_YEARS[lord_index] - balance) * dasha_year_days
        mahadasha_start = dt - timedelta(days=elapsed_mahadasha_days)
        now = datetime.now(timezone.utc)
        mahadashas = []
        for major_offset in range(9):
            major_index = (lord_index + major_offset) % 9
            major_lord = DASHA_LORDS[major_index]
            major_years = DASHA_YEARS[major_index]
            major_end = mahadasha_start + timedelta(days=major_years * dasha_year_days)
            bhuktis = []
            bhukti_start = mahadasha_start
            for sub_offset in range(9):
                sub_index = (major_index + sub_offset) % 9
                sub_lord = DASHA_LORDS[sub_index]
                sub_years = major_years * DASHA_YEARS[sub_index] / 120
                bhukti_end = major_end if sub_offset == 8 else bhukti_start + timedelta(days=sub_years * dasha_year_days)
                bhuktis.append({
                    "lord": sub_lord,
                    "years": round(sub_years, 6),
                    "start_at": bhukti_start.isoformat(),
                    "end_at": bhukti_end.isoformat(),
                    "is_before_birth": bhukti_end <= dt,
                    "is_at_birth": bhukti_start <= dt < bhukti_end,
                    "is_current": bhukti_start <= now < bhukti_end,
                })
                bhukti_start = bhukti_end
            mahadashas.append({
                "lord": major_lord,
                "years": major_years,
                "start_at": mahadasha_start.isoformat(),
                "end_at": major_end.isoformat(),
                "balance_years_at_birth": round(balance, 4) if major_offset == 0 else None,
                "bhuktis": bhuktis,
            })
            mahadasha_start = major_end
        dasha = {"birth_mahadasha": DASHA_LORDS[lord_index], "balance_years_at_birth": round(balance, 4),
                 "year_days": dasha_year_days,
                 "sequence": [{"lord": DASHA_LORDS[(lord_index + i) % 9], "years": DASHA_YEARS[(lord_index + i) % 9]} for i in range(9)],
                 "mahadashas": mahadashas}
        navamsa_lagna = _navamsa(ascendant)
        navamsa_lagna_index = SIGNS.index(navamsa_lagna)
        navamsa_planets = []
        for planet in planets:
            navamsa_sign = planet["navamsa"]
            navamsa_sign_index = SIGNS.index(navamsa_sign)
            navamsa_longitude = (navamsa_sign_index * 30 + (planet["longitude"] % (30 / 9)) * 9) % 360
            navamsa_planets.append({
                "name": planet["name"],
                "rasi": navamsa_sign,
                "longitude": round(navamsa_longitude, 6),
                "house": (navamsa_sign_index - navamsa_lagna_index) % 12 + 1,
            })
        navamsa_chart = {
            "lagna": navamsa_lagna,
            "lagna_longitude": round((navamsa_lagna_index * 30 + (ascendant % (30 / 9)) * 9) % 360, 6),
            "planets": navamsa_planets,
            "houses": [
                {"house": index + 1, "rasi": SIGNS[(navamsa_lagna_index + index) % 12]}
                for index in range(12)
            ],
        }
        lagna_index = SIGNS.index(sign_name(ascendant))
        rasi_chart = {
            "lagna": sign_name(ascendant),
            "lagna_longitude": round(ascendant, 6),
            "planets": [
                {"name": planet["name"], "rasi": planet["rasi"],
                 "longitude": planet["longitude"], "house": (SIGNS.index(planet["rasi"]) - lagna_index) % 12 + 1}
                for planet in planets
            ],
            "houses": [
                {"house": index + 1, "rasi": SIGNS[(lagna_index + index) % 12]}
                for index in range(12)
            ],
        }
        chart = {"ayanamsa": "Lahiri", "lagna": sign_name(ascendant), "lagna_longitude": round(ascendant, 6),
                 "rasi": moon["rasi"], "nakshatra": NAKSHATRAS[nak_index], "planets": planets,
                 "houses": [{"house": i + 1, "longitude": round(float(cusps[i]), 6)} for i in range(12)],
                 "rasi_chart": rasi_chart, "navamsa_chart": navamsa_chart, "dasha": dasha}
        return localize_chart(chart, language)
    except Exception as exc:
        raise HTTPException(422, f"Could not calculate chart: {exc}") from exc






