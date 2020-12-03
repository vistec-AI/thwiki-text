import re
import glob
import os
import argparse
import jsonlines
import itertools
import time
import unicodedata

from typing import List, Dict, Optional
from tqdm.auto import tqdm
from pydantic import BaseModel


class WikiArticle(BaseModel):
    docid: int
    url: str
    title: str
    text: str
    segments: Optional[List[str]]

def load_data(input_extracted_dir: str) -> List[WikiArticle]:
    paths = glob.glob(os.path.join(input_extracted_dir, '*/*'))

    thwiki_objs: List[WikiArticle] = []

    for path in paths:
         with jsonlines.open(path, mode='r') as reader:
            for obj in reader:
                wiki_article = WikiArticle(docid=int(obj['id']),
                                           url=obj['url'],
                                           title=obj['title'],
                                           text=obj['text'])
                thwiki_objs.append(wiki_article)
    return thwiki_objs

def remove_empty_parenthesis(segments):
    
    for i, _ in enumerate(segments):
              
        if ' ())' in segments[i]:
            segments[i] = segments[i].replace(' ())', ')')
        if ')()' in segments[i]:
            segments[i] = segments[i].replace(')()', ')')
        if ' () () ' in segments[i]:
            segments[i] = segments[i].replace(' () () ', ' ')
        if ' ()() ' in segments[i]:
            segments[i] = segments[i].replace(' ()() ', ' ')

        if ' () ' in segments[i]:
            segments[i] = segments[i].replace(' () ', ' ')

        if  re.search(r'(Section::::.+[\sก-๙])(\(\))\.$', segments[i]):
            segments[i] = re.sub(r'(Section::::.+[\sก-๙])(\(\))\.$', '\g<1>.', segments[i])

        if "”() " in segments[i]:
            segments[i] = segments[i].replace("”() ", "” ")

        if "'() " in segments[i]:
            segments[i] = segments[i].replace("'() ", "' ")

        if "'() " in segments[i]:
            segments[i] = segments[i].replace("'() ", "' ")
        if "'()." in segments[i]:
            segments[i] = segments[i].replace("'().", "'")
            
        if ' (); ' in segments[i]:
            segments[i] = segments[i].replace(' (); ', ' ')

        if '(),' in segments[i]:
            segments[i] = segments[i].replace('(),', ',')
            
        if '"() ' in segments[i]:
            segments[i] = segments[i].replace('"() ', '" ')
        if '"()' in segments[i]:
            segments[i] = segments[i].replace('"()', '" ')
        if '" ()' in segments[i]:
            segments[i] = segments[i].replace('" ()', '" ')
            
        if re.search(r'"\(\)$', segments[i]):
            segments[i] = re.sub(r'"\(\)$', '"', segments[i])   
        # found " ()" at the end of line
        if re.search(r'\s\(\)$', segments[i]):
            segments[i] = re.sub(r'\s\(\)$', '', segments[i])
        # found " ()" at the beginning of line
        if re.search(r'^\(\)\s', segments[i]):
            segments[i] = re.sub(r'^\(\)\s', '', segments[i])

        if re.search(r'([ก-๙])\(\)\s', segments[i]):
            segments[i] = re.sub(r'([ก-๙])(\(\)\s)', '\g<1>', segments[i])
        if re.search(r'([ก-๙])\(\)([ก-๙])', segments[i]):
            segments[i] = re.sub(r'([ก-๙])\(\)([ก-๙])', '\g<1> \g<2>', segments[i])

        if re.search(r"(')\(\)([ก-๙])", segments[i]):
            segments[i] = re.sub(r"(')\(\)([ก-๙])", '\g<1> \g<2>', segments[i] )
        if re.search(r"([ก-๙])\(\)", segments[i]):
            segments[i] = re.sub(r"([ก-๙])\(\)", '\g<1>', segments[i] )

        if re.search(r"^\(\)([ก-๙])", segments[i]):
            segments[i] = re.sub(r"^\(\)([ก-๙])", '\g<1>', segments[i] )
        
        if "]()" in segments[i]:
            segments[i] = segments[i].replace("]()", "]")
        if "[()" in segments[i]:
            segments[i] = segments[i].replace("[()", "[")
        if ";()" in segments[i]:
            segments[i] = segments[i].replace(";()", ";")
        if ",()" in segments[i]:
            segments[i] = segments[i].replace(",()", ",")
        if ' ()' in segments[i]:
            segments[i] = segments[i].replace(' ()', ' ')
    return segments


def extract_segmetns(text: str, rm_empty_parenthesis=False) -> List[str]:

    newline = '\n'
    double_newlines = '\n\n'
    segments = []
    # split by \n\n
    segments = text.split(double_newlines)
    # Further split by \n
    nested_segments = [ s.split(newline) for s in segments]
    segments = list(itertools.chain(*nested_segments))
   
    
    segments = list(map(str.strip, segments))
    segments = list(filter(lambda x: len(x) != 0, segments))

    # replace NO-BREAK SPACE (b'\xc2\a0') to SPACE (" ")
    segments = list(map(lambda x: unicodedata.normalize('NFKD', x), segments))
            

    if remove_empty_parenthesis:
        segments = remove_empty_parenthesis(segments)

    # Adding "= {title} =" for the article title
    segments[0] = f'= {segments[0]} =\n'

    # Adding "= = {section} = =" for the article section
    for i, segment in enumerate(segments):
        if 'Section::::' in segment:
            section_text = segment[len('Section::::'):-1]
            segments[i] = f'\n= = {section_text.strip()} = =\n'

    return segments


if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument('input_extracted_dir', help='Path to the directory storing extracted data.')
    parser.add_argument('output_path', help='Path to the directory storing extracted data.')

    parser.add_argument('--rm_empty_parenthesis', action='store_true', help='Remove empty parenthesis from text')


    args = parser.parse_args()


    
    print(f'Loading data from {args.input_extracted_dir}')

    thwiki_objs = load_data(args.input_extracted_dir)

    print(f'\nPreprocess data.')
    print(f'Argument: rm_empty_parenthesis == {args.rm_empty_parenthesis}\n')
    start = time.time()
    for obj in tqdm(thwiki_objs):

        obj.segments = extract_segmetns(obj.text, rm_empty_parenthesis=args.rm_empty_parenthesis)
    
    print(f'\nDone.\nTime taken: {time.time() - start:2f} secs.\n')

    print(f'\nWriting the result to {args.output_path}')

    with open(args.output_path, 'w', encoding='utf-8') as writer:
        for obj in thwiki_objs:
        
            joined_segments = '\n'.join(obj.segments)
            writer.write(f"{joined_segments}\n\n\n")