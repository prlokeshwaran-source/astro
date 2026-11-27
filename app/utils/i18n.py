from typing import Literal
from fastapi import HTTPException
LanguageCode = Literal["en", "ta", "hi"]
LANGUAGES = [
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "ta", "name": "Tamil", "native_name": "தமிழ்"},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
]
SIGNS = {
    "en": ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"],
    "ta": ["மேஷம்", "ரிஷபம்", "மிதுனம்", "கடகம்", "சிம்மம்", "கன்னி", "துலாம்", "விருச்சிகம்", "தனுசு", "மகரம்", "கும்பம்", "மீனம்"],
    "hi": ["मेष", "वृषभ", "मिथुन", "कर्क", "सिंह", "कन्या", "तुला", "वृश्चिक", "धनु", "मकर", "कुंभ", "मीन"],
}
NAKSHATRAS = {
    "en": ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"],
    "ta": ["அசுவினி", "பரணி", "கார்த்திகை", "ரோகிணி", "மிருகசீரிடம்", "திருவாதிரை", "புனர்பூசம்", "பூசம்", "ஆயில்யம்", "மகம்", "பூரம்", "உத்திரம்", "ஹஸ்தம்", "சித்திரை", "சுவாதி", "விசாகம்", "அனுஷம்", "கேட்டை", "மூலம்", "பூராடம்", "உத்திராடம்", "திருவோணம்", "அவிட்டம்", "சதயம்", "பூரட்டாதி", "உத்திரட்டாதி", "ரேவதி"],
    "hi": ["अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा", "पुनर्वसु", "पुष्य", "आश्लेषा", "मघा", "पूर्वाफाल्गुनी", "उत्तराफाल्गुनी", "हस्त", "चित्रा", "स्वाति", "विशाखा", "अनुराधा", "ज्येष्ठा", "मूल", "पूर्वाषाढ़ा", "उत्तराषाढ़ा", "श्रवण", "धनिष्ठा", "शतभिषा", "पूर्वाभाद्रपद", "उत्तराभाद्रपद", "रेवती"],
}
PLANETS = {
    "en": {"Sun":"Sun", "Moon":"Moon", "Mars":"Mars", "Mercury":"Mercury", "Jupiter":"Jupiter", "Venus":"Venus", "Saturn":"Saturn", "Rahu":"Rahu", "Ketu":"Ketu"},
    "ta": {"Sun":"சூரியன்", "Moon":"சந்திரன்", "Mars":"செவ்வாய்", "Mercury":"புதன்", "Jupiter":"குரு", "Venus":"சுக்கிரன்", "Saturn":"சனி", "Rahu":"ராகு", "Ketu":"கேது"},
    "hi": {"Sun":"सूर्य", "Moon":"चंद्र", "Mars":"मंगल", "Mercury":"बुध", "Jupiter":"बृहस्पति", "Venus":"शुक्र", "Saturn":"शनि", "Rahu":"राहु", "Ketu":"केतु"},
}
def validate_language(language: str) -> str:
    if language not in {"en", "ta", "hi"}:
        raise HTTPException(422, "language must be one of: en, ta, hi")
    return language
def language_list() -> list[dict[str, str]]:
    return LANGUAGES
def localize_chart(chart: dict, language: str) -> dict:
    language = validate_language(language)
    result = dict(chart)
    result["language"] = language
    result["lagna_display"] = SIGNS[language][SIGNS["en"].index(chart["lagna"])]
    result["rasi_display"] = SIGNS[language][SIGNS["en"].index(chart["rasi"])]
    result["nakshatra_display"] = NAKSHATRAS[language][NAKSHATRAS["en"].index(chart["nakshatra"])]
    result["planets"] = [{**planet, "name_display": PLANETS[language][planet["name"]],
        "rasi_display": SIGNS[language][SIGNS["en"].index(planet["rasi"])],
        "navamsa_display": SIGNS[language][SIGNS["en"].index(planet["navamsa"])]} for planet in chart["planets"]]
    for chart_key in ("rasi_chart", "navamsa_chart"):
        if chart_key in chart:
            divisional_chart = dict(chart[chart_key])
            divisional_chart["lagna_display"] = SIGNS[language][SIGNS["en"].index(divisional_chart["lagna"])]
            divisional_chart["planets"] = [{**planet,
                "name_display": PLANETS[language][planet["name"]],
                "rasi_display": SIGNS[language][SIGNS["en"].index(planet["rasi"])],
            } for planet in divisional_chart["planets"]]
            divisional_chart["houses"] = [{**house,
                "rasi_display": SIGNS[language][SIGNS["en"].index(house["rasi"])],
            } for house in divisional_chart["houses"]]
            result[chart_key] = divisional_chart
    if "dasha" in chart:
        dasha = dict(chart["dasha"])
        dasha["birth_mahadasha_display"] = PLANETS[language][dasha["birth_mahadasha"]]
        dasha["sequence"] = [{**period, "lord_display": PLANETS[language][period["lord"]]} for period in dasha["sequence"]]
        dasha["mahadashas"] = [{
            **major,
            "lord_display": PLANETS[language][major["lord"]],
            "bhuktis": [{**subperiod, "lord_display": PLANETS[language][subperiod["lord"]]} for subperiod in major["bhuktis"]],
        } for major in dasha.get("mahadashas", [])]
        result["dasha"] = dasha
    return result
