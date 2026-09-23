import json

from pyannote.core import Annotation, Segment

from diarization.diarizer import normalize


def make_annotation(turns):
    annotation = Annotation()
    for i, (start, end, label) in enumerate(turns):
        annotation[Segment(start, end), i] = label
    return annotation


def test_schema_and_types():
    segments = normalize(make_annotation([(0.5, 2.0, "A")]))
    assert segments == [{"speaker": "SPEAKER_00", "start": 0.5, "end": 2.0}]
    segment = segments[0]
    assert type(segment["speaker"]) is str
    assert type(segment["start"]) is float and type(segment["end"]) is float


def test_rounds_to_three_decimals():
    segments = normalize(make_annotation([(0.123456, 4.987654, "A")]))
    assert segments[0]["start"] == 0.123
    assert segments[0]["end"] == 4.988


def test_sorted_by_start():
    segments = normalize(make_annotation([(5.0, 6.0, "A"), (1.0, 2.0, "B"), (3.0, 4.0, "A")]))
    assert [s["start"] for s in segments] == [1.0, 3.0, 5.0]


def test_labels_follow_first_appearance():
    # pyannote etiketleri keyfi; ilk konuşan SPEAKER_00 olmalı.
    segments = normalize(make_annotation([(4.0, 5.0, "SPEAKER_00"), (0.0, 1.0, "SPEAKER_01"), (2.0, 3.0, "X")]))
    assert [s["speaker"] for s in segments] == ["SPEAKER_00", "SPEAKER_01", "SPEAKER_02"]
    assert segments[0]["start"] == 0.0


def test_same_speaker_keeps_same_label():
    segments = normalize(make_annotation([(0.0, 1.0, "B"), (1.5, 2.0, "A"), (2.5, 3.0, "B")]))
    assert [s["speaker"] for s in segments] == ["SPEAKER_00", "SPEAKER_01", "SPEAKER_00"]


def test_overlap_is_preserved():
    segments = normalize(make_annotation([(0.0, 4.0, "A"), (3.0, 6.0, "B")]))
    assert segments == [
        {"speaker": "SPEAKER_00", "start": 0.0, "end": 4.0},
        {"speaker": "SPEAKER_01", "start": 3.0, "end": 6.0},
    ]


def test_empty_annotation_returns_empty_list():
    assert normalize(Annotation()) == []


def test_json_serializable():
    segments = normalize(make_annotation([(0.0, 1.0, "A"), (0.5, 2.0, "B")]))
    assert json.loads(json.dumps(segments)) == segments
