"""Regression checks for observed timestamp integrity; no ASR or network use."""
import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('timing',Path(__file__).with_name('prepare_timeline.py'))
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)


def fixture(expected, recognized, duration=10):
    chapter={'id':'hook','text':expected}
    script=[{'id':'s01','chapter':'hook','text':expected}]
    words=[{'word':c,'start':i*.25+.1,'end':(i+1)*.25+.1,'probability':.99} for i,c in enumerate(recognized)]
    cache={'source_sha256':'test','recognized_text':recognized,'words':words,
           'audio_info':{'duration':duration},'silence':{'-42':[]}}
    return chapter,script,cache


class TimingRegressionTests(unittest.TestCase):
    def test_punctuation_not_lost(self):
        text='他说：“慢慢来。”（不勉强。）'
        self.assertEqual(''.join(t.split_caption_text(text)),text)

    def test_missing_caption_onset_blocks_publication(self):
        args=fixture('甲乙丙丁戊己庚辛。未知。','甲乙丙丁戊己庚辛知')
        row=t.aligned_chapter(*args)
        self.assertTrue(any('missing caption boundary' in x for x in row['errors']))

    def test_unrelated_caption_cannot_borrow_other_sentence_confidence(self):
        args=fixture('甲乙丙丁戊己庚辛。未知。','甲乙丙丁戊己庚辛错字')
        row=t.aligned_chapter(*args)
        self.assertTrue(any('no exact lexical anchor' in x for x in row['errors']))

    def test_asr_clock_outside_audio_is_rejected(self):
        args=fixture('甲乙。','甲乙',duration=3)
        args[2]['words'][-1]['end']=9
        self.assertTrue(t.aligned_chapter(*args)['errors'])

    def test_shared_word_clock_not_divided_by_characters(self):
        args=fixture('甲乙丙丁戊己，庚辛壬癸。','甲乙丙丁戊己庚辛壬癸')
        args[2]['words']=[{'word':'甲乙丙丁戊己庚辛壬癸','start':.2,'end':2.2,'probability':.99}]
        row=t.aligned_chapter(*args)
        self.assertEqual(len(row['captions']),1)
        self.assertEqual(row['captions'][0]['speech_start'],.2)
        self.assertEqual(row['captions'][0]['speech_end'],2.2)

    def test_asr_difference_is_retained(self):
        args=fixture('甲乙丙丁。','甲异丙丁')
        row=t.aligned_chapter(*args)
        self.assertEqual(row['recognized_text'],'甲异丙丁')
        self.assertEqual(row['differences'][0]['expected'],'乙')
        self.assertEqual(row['differences'][0]['recognized'],'异')
        self.assertTrue(row['needs_review'])

    def test_estimated_global_boundaries_stay_on_frame_grid(self):
        specs=[{'id':'hook','text':'甲乙丙。'},{'id':'title','text':''}]
        script={'title':'test','segments':[{'id':'s01','chapter':'hook','text':'甲乙丙。'},
                 {'id':'s03','chapter':'title','text':''}]}
        rows={'hook':t.estimated_alignment(specs[0],script['segments'])}
        result=t.assemble(specs,script,rows,{},estimated=True)
        for cap in result['captions']:
            self.assertEqual(cap['start'],cap['start_frame']/30)
            self.assertEqual(cap['end'],cap['end_frame']/30)
        self.assertEqual(result['duration'],result['frame_count']/30)
        self.assertEqual(result['cuts'],[frame/30 for frame in result['cut_frames']])

if __name__=='__main__':unittest.main()
