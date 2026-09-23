import json

from transcription.transcript import attach_text, build_transcript


def seg(speaker, start, end):
    return {"speaker": speaker, "start": start, "end": end}


def word(start, end, text):
    return {"start": start, "end": end, "text": text}


def texts(segments):
    return [s["text"] for s in segments]


def test_word_inside_segment():
    segments = [seg("SPEAKER_00", 0.0, 2.0), seg("SPEAKER_01", 3.0, 5.0)]
    result = attach_text(segments, [word(0.5, 1.0, " merhaba"), word(3.5, 4.0, " selam")])
    assert texts(result) == ["merhaba", "selam"]


def test_word_spanning_two_segments_goes_to_larger_overlap():
    segments = [seg("SPEAKER_00", 0.0, 2.0), seg("SPEAKER_01", 2.0, 4.0)]
    result = attach_text(segments, [word(1.8, 2.5, " kelime")])  # 0.2 sn A, 0.5 sn B
    assert texts(result) == ["", "kelime"]


def test_equal_overlap_goes_to_earlier_segment():
    # İki konuşmacının çakıştığı bölge: iki segmentle de 0.5 sn örtüşüyor.
    segments = [seg("SPEAKER_00", 0.0, 3.0), seg("SPEAKER_01", 2.0, 5.0)]
    result = attach_text(segments, [word(2.2, 2.7, " aynı")])
    assert texts(result) == ["aynı", ""]


def test_word_outside_segments_within_tolerance_goes_to_nearest():
    segments = [seg("SPEAKER_00", 0.0, 1.0), seg("SPEAKER_01", 5.0, 6.0)]
    result = attach_text(segments, [word(1.3, 1.6, " yakın")])  # A'ya 0.3 sn
    assert texts(result) == ["yakın", ""]


def test_word_exactly_at_tolerance_is_assigned():
    segments = [seg("SPEAKER_00", 0.0, 2.3)]
    result = attach_text(segments, [word(2.8, 3.0, " sınır")])  # boşluk tam 0.5 sn
    assert texts(result) == ["sınır"]


def test_word_beyond_tolerance_is_dropped():
    segments = [seg("SPEAKER_00", 0.0, 2.3), seg("SPEAKER_01", 5.0, 6.0)]
    result = attach_text(segments, [word(2.801, 3.0, " uzak")])  # en yakın boşluk 0.501 sn
    assert texts(result) == ["", ""]


def test_segment_without_words_is_kept():
    segments = [seg("SPEAKER_00", 0.0, 1.0), seg("SPEAKER_01", 1.0, 1.07)]
    result = attach_text(segments, [word(0.1, 0.6, " tek")])
    assert result == [
        {"speaker": "SPEAKER_00", "start": 0.0, "end": 1.0, "text": "tek"},
        {"speaker": "SPEAKER_01", "start": 1.0, "end": 1.07, "text": ""},
    ]


def test_words_joined_and_stripped():
    segments = [seg("SPEAKER_00", 0.0, 3.0)]
    result = attach_text(segments, [word(0.0, 0.5, " Bugün"), word(0.6, 1.0, " toplantı"), word(1.1, 1.5, " var.")])
    assert texts(result) == ["Bugün toplantı var."]


def test_no_segments():
    transcript = build_transcript("sessiz.wav", [], [word(0.0, 1.0, " kayıp")])
    assert transcript == {"source_file": "sessiz.wav", "speaker_count": 0, "segments": []}


def test_build_transcript_fields_and_json():
    segments = [seg("SPEAKER_00", 0.82, 5.41), seg("SPEAKER_01", 5.68, 9.92), seg("SPEAKER_00", 10.0, 11.0)]
    words = [word(1.0, 2.0, " Bugünkü"), word(6.0, 7.0, " Öncelikle")]
    transcript = build_transcript("meeting.wav", segments, words)
    assert list(transcript) == ["source_file", "speaker_count", "segments"]
    assert transcript["speaker_count"] == 2
    assert list(transcript["segments"][0]) == ["speaker", "start", "end", "text"]
    assert json.loads(json.dumps(transcript, ensure_ascii=False)) == transcript


def test_input_segments_not_mutated():
    segments = [seg("SPEAKER_00", 0.0, 1.0)]
    attach_text(segments, [word(0.1, 0.5, " x")])
    assert segments == [seg("SPEAKER_00", 0.0, 1.0)]
