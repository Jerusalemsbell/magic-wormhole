from __future__ import print_function
import os, sys, six
from .wordlist import (byte_to_even_word, byte_to_odd_word,
                       even_words_lowercase, odd_words_lowercase)

def make_code(channel_id, code_length):
    assert isinstance(channel_id, type(u"")), type(channel_id)
    words = []
    for i in range(code_length):
        # we start with an "odd word"
        if i % 2 == 0:
            words.append(byte_to_odd_word[os.urandom(1)].lower())
        else:
            words.append(byte_to_even_word[os.urandom(1)].lower())
    return u"%s-%s" % (channel_id, u"-".join(words))

def extract_channel_id(code):
    channel_id = int(code.split("-")[0])
    return channel_id

class CodeInputter:
    def __init__(self, initial_channelids, get_channel_ids, code_length):
        self._initial_channelids = initial_channelids
        self._get_channel_ids = get_channel_ids
        self.code_length = code_length
        self.last_text = None # memoize for a speedup
        self.last_matches = None

    def debug(self, *args, **kwargs):
        if False:
            print(*args, file=sys.stderr, **kwargs)
            sys.stderr.flush()

    def get_current_channel_ids(self):
        if self._initial_channelids is not None:
            channelids = self._initial_channelids
            self._initial_channelids = None
            return channelids
        return self._get_channel_ids()

    def wrap_completer(self, text, state):
        try:
            return self.completer(text, state)
        except Exception as e:
            # completer exceptions are normally silently discarded, which
            # makes debugging challenging
            print("completer exception: %s" % e, file=sys.stderr)
            raise e

    def completer(self, text, state):
        if state == 0:
            self.debug("")
        self.debug("completer: '%s' %d" % (text, state))
        pieces = text.split("-")
        last = pieces[-1].lower()
        if text == self.last_text and len(pieces) >= 2:
            # if len(pieces) == 1, skip the cache, so we can re-fetch the
            # channel_id list
            matches = self.last_matches
            self.debug(" old matches", len(matches))
        else:
            if len(pieces) <= 1:
                channel_ids = self.get_current_channel_ids()
                matches = [str(channel_id) for channel_id in channel_ids
                           if str(channel_id).startswith(last)]
            else:
                if len(pieces) % 2 == 0:
                    words = odd_words_lowercase
                else:
                    words = even_words_lowercase
                so_far = "-".join(pieces[:-1]) + "-"
                matches = sorted([so_far+word for word in words
                                  if word.startswith(last)])
            self.last_text = text
            self.last_matches = matches
            self.debug(" new matches:", matches)
        if state >= len(matches):
            return None
        match = matches[state]
        if len(pieces) < 1+self.code_length:
            match += "-"
        self.debug(" match: '%s'" % match)
        return match


def input_code_with_completion(prompt, initial_channelids, get_channel_ids,
                               code_length):
    try:
        import readline
        c = CodeInputter(initial_channelids, get_channel_ids, code_length)
        if "libedit" in readline.__doc__:
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")
        readline.set_completer(c.wrap_completer)
        readline.set_completer_delims("")
    except ImportError:
        pass
    code = six.moves.input(prompt)
    # Code is str(bytes) on py2, and str(unicode) on py3. We want unicode.
    if isinstance(code, bytes):
        code = code.decode("utf-8")
    return code

if __name__ == "__main__":
    code = input_code_with_completion("Enter wormhole code: ", lambda: [], 2)
    print("code is:", code)
