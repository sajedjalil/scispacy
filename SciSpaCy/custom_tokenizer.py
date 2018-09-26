from spacy.lang import char_classes
from spacy.symbols import ORTH # pylint: disable-msg=E0611,E0401
from spacy.tokenizer import Tokenizer # pylint: disable-msg=E0611,E0401
from spacy.util import compile_prefix_regex, compile_infix_regex, compile_suffix_regex

def remove_new_lines(text):
    # used to preprocess away new lines in the middle of words
    text = text.replace("-\n\n", "")
    text = text.replace("- \n\n", "")
    text = text.replace("-\n", "")
    text = text.replace("- \n", "")
    return text

def combined_rule_prefixes():
    # split into function to accomodate spacy tests
    # add lookahead assertions for brackets (may not work properly for unbalanced brackets)
    prefix_punct = r'… …… , : ; \! \? ¿ ؟ ¡ \((?![^\(\s]+\)\S+) \) \[(?![^\[\s]+\]\S+) \] \{(?![^\{\s]+\}\S+) \} < > _ # \* & 。 ？ ！ ， 、 ； ： ～ · । ، ؛ ٪'
    prefixes = (['§', '%', '=', r'\+'] +
                char_classes.split_chars(prefix_punct) +
                char_classes.LIST_ELLIPSES +
                char_classes.LIST_QUOTES +
                char_classes.LIST_CURRENCY +
                char_classes.LIST_ICONS)
    return prefixes

def combined_rule_tokenizer(nlp):
    # removed the first hyphen to prevent tokenization of the normal hyphen
    hyphens = char_classes.merge_chars('– — -- --- —— ~')
    infixes = (char_classes.LIST_ELLIPSES +
               char_classes.LIST_ICONS +
               [r'×', # added this special x character to tokenize it separately
                r'(?<=[0-9])[+\-\*^](?=[0-9-])',
                r'(?<=[{}])\.(?=[{}])'.format(char_classes.ALPHA_LOWER, char_classes.ALPHA_UPPER),
                r'(?<=[{a}]),(?=[{a}])'.format(a=char_classes.ALPHA),
                r'(?<=[{a}])[?";:=,.]*(?:{h})(?=[{a}])'.format(a=char_classes.ALPHA, h=hyphens),
                r'(?<=[{a}"])[:<>=](?=[{a}])'.format(a=char_classes.ALPHA)]) # removed / to prevent tokenization of /

    prefixes = combined_rule_prefixes()

    # add the last apostrophe
    quotes = r'\' \'\' " ” “ `` ` ‘ ´ ‘‘ ’’ ‚ , „ » « 「 」 『 』 （ ） 〔 〕 【 】 《 》 〈 〉 ’'
    # add lookbehind assertions for brackets (may not work properly for unbalanced brackets)
    suffix_punct = r'… …… , : ; \! \? ¿ ؟ ¡ \( (?<!\S+\([^\)\s]+)\) \[ (?<!\S+\[[^\]\s]+)\] \{ (?<!\S+\{[^\}\s]+)\} < > _ # \* & 。 ？ ！ ， 、 ； ： ～ · । ، ؛ ٪'
    suffixes = (char_classes.split_chars(suffix_punct) +
                char_classes.LIST_ELLIPSES +
                char_classes.split_chars(quotes) +
                char_classes.LIST_ICONS +
                ["'s", "'S", "’s", "’S", "’s", "’S"] +
                [r'(?<=[0-9])\+',
                 r'(?<=°[FfCcKk])\.',
                 r'(?<=[0-9])(?:{})'.format(char_classes.CURRENCY),
                 r'(?<=(^[0-9]+|\s{p}*[0-9]+))(?:{u})'.format(u=char_classes.UNITS, p=prefixes), # add to look behind to exclude things like h3g from splitting off the g as a unit
                 r'(?<=[0-9{}{}(?:{})])\.'.format(char_classes.ALPHA_LOWER, r'%²\-\)\]\+', char_classes.merge_chars(quotes)),
                 r'(?<=[{a}|\d][{a}])\.'.format(a=char_classes.ALPHA_UPPER)]) # add |\d to split off the period of a sentence that ends with 1D.
    infix_re = compile_infix_regex(infixes)
    prefix_re = compile_prefix_regex(prefixes)
    suffix_re = compile_suffix_regex(suffixes)

    # Update exclusions to include these abbreviations so the period is not split off
    exclusions = {"sec.": [{ORTH: "sec."}],
                  "secs.": [{ORTH: "secs."}],
                  "Sec.": [{ORTH: "Sec."}],
                  "Secs.": [{ORTH: "Secs."}],
                  "fig.": [{ORTH: "fig."}],
                  "figs.": [{ORTH: "figs."}],
                  "Fig.": [{ORTH: "Fig."}],
                  "Figs.": [{ORTH: "Figs."}],
                  "eq.": [{ORTH: "eq."}],
                  "eqs.": [{ORTH: "eqs."}],
                  "Eq.": [{ORTH: "Eq."}],
                  "Eqs.": [{ORTH: "Eqs."}],
                  "no.": [{ORTH: "no."}],
                  "nos.": [{ORTH: "nos."}],
                  "No.": [{ORTH: "No."}],
                  "Nos.": [{ORTH: "Nos."}],
                  "al.": [{ORTH: "al."}]}
    tokenizer_exceptions = nlp.Defaults.tokenizer_exceptions.copy()
    tokenizer_exceptions.update(exclusions)

    tokenizer = Tokenizer(nlp.vocab, tokenizer_exceptions, prefix_search=prefix_re.search, suffix_search=suffix_re.search, infix_finditer=infix_re.finditer, token_match=nlp.tokenizer.token_match)
    return tokenizer
