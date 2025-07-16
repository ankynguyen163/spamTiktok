def clean_caption(text):
    # Cắt phần sau \n nếu có
    if '\\n' in text:
        text = text.split('\\n')[0].strip()

    # Cắt phần sau # nếu có
    if '#' in text:
        text = text.split('#')[0].strip()
    # Cắt phần sau " | " nếu có
    if '|' in text:
        text = text.split('|')[0].strip()
    # Cắt phần sau ©️ nếu có
    if '©️' in text:
        text = text.split('©️')[0].strip()
    return text

def generate_hashtags():
    return "#toolTải&Upclip-->Tiktoktựđộng"