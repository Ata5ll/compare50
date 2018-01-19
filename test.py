import sys
import os
import pprint
from termcolor import colored
from preprocessors.nop import Nop
from preprocessors.token_processor import *
from comparators.winnowing import Winnowing

from compare import compare


def preprocess_and_fingerprint():
    _, ext = os.path.splitext(sys.argv[1])
    if ext == ".py":
        lang = "Python3"
    elif ext == ".c":
        lang = "C"
    preprocessor = TokenProcessor(
        lang,
        # StripWhitespace(),
        # StripComments(),
        # NormalizeIdentifiers(),
        NormalizeStringLiterals(),
        # NormalizeNumericLiterals(),
        # ExtractIdentifiers(),
        TokenPrinter(),
        Buffer(),
        TextPrinter()
    )
    comparator = Winnowing(preprocessor, 12, 24)
    result = comparator.create_index(sys.argv[1], None)
    print(result)
    print(len(repr(result)))


def compare_two():
    def index(filename):
        preprocessor = Nop()
        comparator = Winnowing(16, 24)
        return comparator.create_index(filename, preprocessor)
    index1 = index(sys.argv[1])
    index2 = index(sys.argv[2])
    print(index1.compare(index2))


def similarities():
    directory = sys.argv[1]
    submission_dirs = [f"{directory}/{d}"
                       for d in os.listdir(f"{directory}")
                       if os.path.isdir(f"{directory}/{d}")]
    submissions = [tuple(f"{d}/{f}" for f in os.listdir(d)
                         if os.path.isfile(f"{d}/{f}"))
                   for d in submission_dirs]
    distro = ("similarities/helpers.py",)
    results = compare(distro, submissions)
    # pp = pprint.PrettyPrinter(width=1, indent=1, compact=True)
    # pp.pprint(results)

    def sort_fn(pair):
        all_score = (results[pair].get("strip_all") or [0])[0]
        ws_score = (results[pair].get("strip_ws") or [0])[0]
        return all_score + ws_score

    top_matches = sorted(results.keys(), key=sort_fn, reverse=True)[:8]
    report(results[key] for key in top_matches)


def highlight(spans, text, color="red"):
    if not spans:
        return text
    non_match = [text[:spans[0].start]]
    for i in range(1, len(spans)):
        non_match.append(text[spans[i-1].stop:spans[i].start])
    match = [colored(text[s.start:s.stop], color) for s in spans]
    combined = []
    for i in range(len(non_match) + len(match)):
        if i % 2 == 0:
            combined.append(non_match.pop(0))
        else:
            combined.append(match.pop(0))
    return "".join(combined)


def report(results):
    def write_report(filename, spans, score):
        files = set(span.file for span in spans)
        by_file = {file: [] for file in files}
        for span in spans:
            by_file[span.file].append(span)
        with open(filename, "w") as output:
            output.write(f"score: {score}\n")
            for file, spans in by_file.items():
                with open(file, "r") as f:
                    text = f.read()
                output.write(file)
                output.write("\n\n")
                output.write(highlight(Span.coalesce(spans), text))
                output.write("\n\n")

    for i, result in enumerate(results):
        all_spans1 = []
        all_spans2 = []
        cum_score = 0
        for pass_name, (score, spans) in result.items():
            spans1, spans2 = zip(*spans)
            spans1 = [s for span_set in spans1 for s in span_set]
            spans2 = [s for span_set in spans2 for s in span_set]
            write_report(f"out{i}a-{pass_name}.txt", spans1, score)
            write_report(f"out{i}b-{pass_name}.txt", spans2, score)
            all_spans1.extend(spans1)
            all_spans2.extend(spans2)
            cum_score += score
        write_report(f"out{i}a-all.txt", all_spans1, cum_score)
        write_report(f"out{i}b-all.txt", all_spans2, cum_score)


if __name__ == "__main__":
    # preprocess_and_fingerprint()
    # compare_two()
    similarities()