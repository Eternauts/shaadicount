"""What we say back, in the household's language.

Fixed templates, not LLM text: the spoken number must always match the saved number.
"""

ATTENDING = {
    "hi-IN": "बहुत-बहुत धन्यवाद! हमने मेहमानों की गिनती {plates} लिख ली है{diet}। शादी में आपका इंतज़ार रहेगा!",
    "kn-IN": "ತುಂಬಾ ಧನ್ಯವಾದಗಳು! ಅತಿಥಿಗಳ ಸಂಖ್ಯೆ {plates} ಎಂದು ಬರೆದುಕೊಂಡಿದ್ದೇವೆ{diet}. ಮದುವೆಯಲ್ಲಿ ನಿಮ್ಮನ್ನು ಎದುರು ನೋಡುತ್ತೇವೆ!",
    "ta-IN": "மிக்க நன்றி! விருந்தினர் எண்ணிக்கை {plates} என்று குறித்துக்கொண்டோம்{diet}. திருமணத்தில் உங்களை எதிர்பார்க்கிறோம்!",
    "en-IN": "Thank you so much! We have noted a guest count of {plates}{diet}. We look forward to seeing you at the wedding!",
}
DECLINED = {
    "hi-IN": "बताने के लिए धन्यवाद। शादी में आपकी कमी ज़रूर महसूस होगी!",
    "kn-IN": "ತಿಳಿಸಿದ್ದಕ್ಕೆ ಧನ್ಯವಾದಗಳು. ಮದುವೆಯಲ್ಲಿ ನಿಮ್ಮನ್ನು ಖಂಡಿತ ಮಿಸ್ ಮಾಡಿಕೊಳ್ಳುತ್ತೇವೆ!",
    "ta-IN": "தெரிவித்ததற்கு நன்றி. திருமணத்தில் உங்களை நிச்சயம் மிஸ் பண்ணுவோம்!",
    "en-IN": "Thank you for letting us know. We will miss you at the wedding!",
}
# "mixed" adds nothing: it also covers guests who did not mention food.
DIET = {
    "hi-IN": {"veg": ", और खाना शाकाहारी रहेगा", "non_veg": ", और खाना मांसाहारी रहेगा", "jain": ", और खाना जैन रहेगा"},
    "kn-IN": {"veg": ", ಊಟ ಸಸ್ಯಾಹಾರಿ", "non_veg": ", ಊಟ ಮಾಂಸಾಹಾರಿ", "jain": ", ಜೈನ ಊಟ"},
    "ta-IN": {"veg": ", சைவ உணவு", "non_veg": ", அசைவ உணவு", "jain": ", ஜெயின் உணவு"},
    "en-IN": {"veg": ", with vegetarian food", "non_veg": ", with non-vegetarian food", "jain": ", with Jain food"},
}


def confirmation(language: str, saved: dict) -> str:
    if not saved["attending"]:
        return DECLINED[language]
    return ATTENDING[language].format(
        plates=saved["headcount"] + saved["plus_ones"],
        diet=DIET[language].get(saved["diet"], ""),
    )


REFUSALS = {
    "plus_ones_not_allowed": {
        "hi-IN": "माफ़ कीजिए, यह निमंत्रण {invited} लोगों के लिए है, इसलिए हम अतिरिक्त मेहमान नहीं जोड़ पाएँगे। कृपया अपने परिवार की गिनती बताइए।",
        "kn-IN": "ಕ್ಷಮಿಸಿ, ಈ ಆಮಂತ್ರಣ {invited} ಜನರಿಗೆ ಮಾತ್ರ, ಹೆಚ್ಚುವರಿ ಅತಿಥಿಗಳನ್ನು ಸೇರಿಸಲು ಆಗುವುದಿಲ್ಲ. ದಯವಿಟ್ಟು ನಿಮ್ಮವರು ಎಷ್ಟು ಜನ ಎಂದು ತಿಳಿಸಿ.",
        "ta-IN": "மன்னிக்கவும், இந்த அழைப்பு {invited} பேருக்கு மட்டும், கூடுதல் விருந்தினர்களைச் சேர்க்க முடியாது. உங்கள் குடும்பத்தில் எத்தனை பேர் என்று சொல்லுங்கள்.",
        "en-IN": "Sorry, this invitation is for {invited} people, so we cannot add extra guests. Please tell us how many of your own group are coming.",
    },
    "catering_locked": {
        "hi-IN": "माफ़ कीजिए, खाने की गिनती अब पक्की हो चुकी है, इसलिए हम इसे बदल नहीं पाएँगे।",
        "kn-IN": "ಕ್ಷಮಿಸಿ, ಊಟದ ಸಂಖ್ಯೆ ಈಗ ಅಂತಿಮವಾಗಿದೆ, ಇನ್ನು ಬದಲಾಯಿಸಲು ಆಗುವುದಿಲ್ಲ.",
        "ta-IN": "மன்னிக்கவும், உணவு எண்ணிக்கை இப்போது இறுதி செய்யப்பட்டுவிட்டது, இனி மாற்ற முடியாது.",
        "en-IN": "Sorry, the catering count is now final, so we cannot change it.",
    },
    "not_understood": {
        "hi-IN": "माफ़ कीजिए, समझ नहीं आया। कृपया बताइए कितने लोग आ रहे हैं, और खाना वेज या नॉन-वेज?",
        "kn-IN": "ಕ್ಷಮಿಸಿ, ಅರ್ಥವಾಗಲಿಲ್ಲ. ಎಷ್ಟು ಜನ ಬರುತ್ತೀರಿ, ಊಟ ವೆಜ್ ಅಥವಾ ನಾನ್-ವೆಜ್ ಎಂದು ತಿಳಿಸಿ.",
        "ta-IN": "மன்னிக்கவும், புரியவில்லை. எத்தனை பேர் வருகிறீர்கள், சைவமா அசைவமா என்று சொல்லுங்கள்.",
        "en-IN": "Sorry, we did not catch that. Please say how many of you are coming, and veg or non-veg.",
    },
}


def refusal(household: dict, code: str) -> str:
    return REFUSALS[code][household["language"]].format(invited=household["invited_count"])
