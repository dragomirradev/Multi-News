import os
import sys
import json
import glob
from nltk.tokenize import ToktokTokenizer
# pip install newspaper3k
from newspaper import fulltext
TOTAL_WORDS = 500

# function to clean data based on observed leftover social media text from html
def clean(line):
    line = line.strip().replace("newline_char", " ")
    line = line.replace("( opens in new window )", "")
    line = line.replace("click to email this to a friend", "")
    line = line.replace("lick to share on whatsapp", "")
    line = line.replace("click to share on facebook", "")
    line = line.replace("share on facebook", "")
    line = line.replace("click to share on twitter", "")
    line = line.replace("click to share on pinterest", "")
    line = line.replace("click to share on tumblr", "")
    line = line.replace("click to share on google+", "")
    line = line.replace("feel free to share these resources in your social "
                        "media networks , websites and other platforms", "")
    line = line.replace("share share tweet link", "")
    line = line.replace("e-mail article print share", "")
    line = line.replace("read or share this story :", "")
    line = line.replace("share the map view in e-mail by clicking the share "
                        "button and copying the link url .     embed the map "
                        "on your website or blog by getting a snippet of html "
                        "code from the share button .     if you wish to "
                        "provide feedback or comments on the map , or if "
                        "you are aware of map layers or other "
                        "datasets that you would like to see included on our maps , "
                        "please submit them for our evaluation using this this form .", "")
    line = line.replace("share this article share tweet post email", "")
    line = line.replace("skip in skip x embed x share close", "")
    line = line.replace("share tweet pin email", "")
    line = line.replace("share on twitter", "")
    line = line.replace("feel free to weigh-in yourself , via"
                        "the comments section . and while you ’ "
                        "re here , why don ’ t you sign up to "
                        "follow us on twitter us on twitter .", "")
    line = line.replace("follow us on facebook , twitter , instagram and youtube", "")
    line = line.replace("follow us on twitter", "")
    line = line.replace("follow us on facebook", "")
    line = line.replace("play facebook twitter google plus embed", "")
    line = line.replace("play facebook twitter embed", "")
    line = line.replace("enlarge icon pinterest icon close icon", "")
    line = line.replace("follow on twitter", "")
    line = line.replace("autoplay autoplay copy this code to your website or blog", "")
    return line

# function to extract main text from Wayback links and tokenize the text
def clean_archive_data(folder):
    toktok = ToktokTokenizer()
    if not os.path.exists(f"{folder}-cleaned"):
        os.makedirs(f"{folder}-cleaned")
    for count, file in enumerate(os.listdir(f"{folder}")):
        if count % 1000 == 0:
            print(count)
        file_data = open(f"{folder}/{file}", "r").read()
        try:
            text_newspaper = toktok.tokenize(fulltext(file_data))
            text_newspaper_cleaned = clean(" ".join(text_newspaper))
            with open(f"{folder}-cleaned/{file}", "w") as output:
                output.write(text_newspaper_cleaned)
        except: # pylint: disable=W0702
            print(f"error with {file}", file=sys.stderr)

def get_split(split):
    with open(f"../final_data/{split}.src.txt", "w") as output_src, \
            open(f"../final_data/{split}.tgt.txt", "w") as output_tgt, \
            open(f"../ids/{split}.id", "r") as input_file:
        for count, line in enumerate(input_file):
            if count % 1000 == 0:
                print(count)
            cur_id = int(line.strip())
            try:
                cur_data = []
                for filename in glob.glob(f"../articles-cleaned/{cur_id}*"):
                    file_data = open(filename, "r").read().replace("\n", " ")
                    cur_data.append(file_data)
                input_str = " story_separator_special_tag ".join(cur_data)
                summary_str = open(f"../summaries-cleaned/{cur_id}",
                                   "r").read().replace("\n", " ")
            except FileNotFoundError:
                print(cur_id)
                continue
            output_src.write(f"{input_str}\n")
            output_tgt.write(f"{summary_str}\n")


def check_available(folder):
    with open("available.txt", "w") as output:
        # TODO directory corresponding to downloaded "availability" WayBack links
        for count, file in enumerate(os.listdir(f"{folder}")):
            if count % 1000 == 0:
                print(count)
            try:
                json_dict = json.load(open(f"{folder}/{file}", "r"))
                url = json_dict["archived_snapshots"]["closest"]["url"]
                output.write(f"{url}\tarticles/{file}\n")
            except KeyError:
                continue

def truncate(split, mode):
    with open(f"{split}.txt.{mode}", "w") as output_file:
        with open(f"copy_data_pre_truncate/{split}.txt.{mode}.final", "r") as input_file:
            for count, line in enumerate(input_file):
                print(count)
                line = line.strip()
                line_word_split = line.split()
                if len(line_word_split) < 500:
                    output_file.write(f"{line}\n")
                else:
                    sources_split = line.split("story_separator_special_tag")
                    num_sources = len(sources_split)
                    num_words_ar = [len(source.split()) for source in sources_split]
                    words_ar = [source.split() for source in sources_split]
                    per_source_count = math.floor(TOTAL_WORDS / num_sources)
                    total_ar = [0] * num_sources
                    # print(f"original word count for each source: {num_words_ar}")
                    total = 0
                    saturated = []
                    # while we haven't used up all the tokens in the array of sents
                    while len(saturated) < num_sources:
                        for inner_count, num in enumerate(num_words_ar):
                            # if we've already filled this entry, just add it to the
                            # total
                            if num in saturated:
                                total += num
                                continue
                            if num < per_source_count:
                                cur_num = num
                                saturated.append(num)
                            else:
                                cur_num = per_source_count
                            total_ar[inner_count] = cur_num
                            total += cur_num
                        if total >= 490:
                            break
                        else:
                            remaining = 500 - total
                            total = 0
                            divide_among = num_sources - len(saturated)
                            if divide_among == 0:
                                break
                            per_source_count += remaining//divide_among
                    # print(len(total_ar))
                    final_words_ar = []
                    for count_words, words in enumerate(words_ar):
                        cur_string = " ".join(words[:total_ar[count_words]])
                        final_words_ar.append(cur_string)
                    final_str = " story_separator_special_tag ".join(final_words_ar).strip()
                    output_file.write(f"{final_str}\n")
                    # print(final_str)
                    # print(f"final word count for each source: {total_ar}")
                    # print("=============================================")

def clean_summary_str(s):
    s = s.lower()
    s = s.replace('<unk>','')
    s = s.replace('`', '')
    s = s.replace('.', '')
    s = s.replace(',', '')
    s = s.replace(';', '')
    s = s.replace('\'', '')
    s = s.replace('\"', '')
    s = s.replace('(', '')
    s = s.replace(')', '')
    s = s.replace('-', ' ')
    s = s.replace('<p>', '')
    s = s.replace('</p>', '')
    s = s.replace('<t>', '')
    s = s.replace('</t>', '')
    s = s.replace('[!@#$]', '')
    return s
                    
if __name__ == "__main__":
    if not os.path.exists("../final_data"):
        os.makedirs("../final_data")
    clean_archive_data("../articles")
    clean_archive_data("../summaries")
    get_split("train")
    get_split("val")
    get_split("test")
