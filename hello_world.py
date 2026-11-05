import regex
import cld3
import langdetect
from textblob import TextBlob


print(cld3.get_language("草🍇🍇🍇❣️💕🍇"))
# Thank you mgaitan https://gist.github.com/Alex-Just/e86110836f3f93fe7932290526529cd1
EMOJI_PATTERN = regex.compile(
    "^["
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F700-\U0001F77F"  # alchemical symbols
    "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA00-\U0001FA6F"  # Chess Symbols
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002702-\U000027B0"  # Dingbats
    "\U000024C2-\U0001F251" 
    "]+$"
)

emoji_spam_pattern = r"^(:_?\w+_?:)+$"
print(regex.match(emoji_spam_pattern, ":_になりました::_peko:"))
emoji = "🍇🍇🍇❣️💕🍇"
print(regex.match(EMOJI_PATTERN, emoji))
text = "867,895 views"
total_comm = "4,600 comments"
pattern = r"^(\d{1,3},)*,?\d{1,3}"
view_count = regex.match(pattern, text).group(0)
view_count = regex.sub(",", "", view_count)
print(int(view_count)/10)
text_wut = "haaaaaaaaaaaachaaaaamaaaaaa chamaaa"
test_slang = regex.match(r"^(ha+ch+a+ma+)/s(ch+a+ma*)$", text_wut)
print(test_slang)
comm_num = regex.match(pattern, total_comm).group(0)
comm_num = regex.sub(",", "", comm_num)
print(comm_num)
scheisse = "wow"
kio = "/wowowow"
scheisse = scheisse + kio
print(scheisse)