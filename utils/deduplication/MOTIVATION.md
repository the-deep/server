# Document De-Duplication

## Story and the problem
- We decided to use AWS KNN which is based on ElasticSearch.
- The documents need to be converted to some kind of vectors which will then be uploaded to KNN index
- Our initial thought was to use the count vectorizer which contained the absolute/relative frequencies of all the words in the document. It seemed promising.
- But as we researched further, it occured that the vectors need to have a fixed size. We can calculate the vector length based on the existing documents and the words in them but accomodating new words in the vector seemed a very challenging problem. *[Do I need to explain why?]*
- On top of that, AWS KNN allows a single vector to have a size limit of 10000. But this should not be a problem as we can use multiple vectors to index documents, each restricted by the 10000 limit.

## Solution Theory
Instead of using words frequencies as vectors, if we use character trigrams frequencies as vectors, then we can have a fixed size of the vector, albeit very large. It is important to note that we will strip the documents of spaces and punctuation letters. The entries of the vectors will be within `0` and `1` obtained by dividing the trigram frequency by total trigrams in the document.

#### English
If we consider the lowercase english characters only, the size of the vector will be `26*26*26 = 17576` which is greater than `10000` but we can just split it up to multiple vectors. 

If we consider using other languages, then depending upon the alphabet set the size can darmatically grow up. We are considering using **Spanish** and **French**.

#### Spanish
Spanish just has an extra `ñ` character so this shouldn't be a problem for vector size. There is just **one more character** to consider.

#### French
However, french has a couple of more characters:
- `ç` - the cedilla (la cédille)
- `é` - the acute accent (l'accent aigu)
- `â` / `ê` / `î` / `ô` / `û` - the circumflex (l'accent circonflexe)
- `à` / `è` / `ì` / `ò` / `ù` – the grave accent (l'accent grave)
- `ë` / `ï` / `ü` - the trema (l'accent tréma)

So, there are **15 more characters** to consider.

### New Vector size
Altogether we now have `26 + 1 + 15 = 42` character sets which will increase the vector size to be `42 * 42 * 42 = 74088`. Given the `10000` size limit for AWS KNN vector, we need to have `8` vectors per document.

### And Numbers ?
Depending upon how much sensitive we want the deduplication to be numbers can be included or excluded.

### Do we really need all of the vector components?
- Having the alphabet size `42` does not necessarily mean all the `74088` combinations of trigrams will appear in the real language(but since we are stripping the spaces and punctuations, many trigrams that would otherwise not appear can appear). So including all the possible trigrams, although seems more precise and accurate representation, might just be an overkill. 
- We can determine which trigrams are most prominent. Since **DEEP** has a vast collection of various crisis related documents, we can use the documents we already have, to come up with an approximate frequencies of the trigrams. **Good thing about this is that we can share this result which some other students/researchers working on similar problem can find quite useful.**
- Now, we can threshold the insignificant trigrams and hopefully reduce the vector size considerably.

**NOTE:** We should probably calculate the frequencies for different languages separately, rather than feeding in the whole corpus DEEP has.

### Enhancements
- Depending upon the results of the above process, we can change the way of calculating trigrams: we strip off the punctuations but let spaces be around. We can treat spaces as part of the alphabet. This probably will be a better approximation than the above.

### Drawback
- Since this method also checks for near duplication, sometimes it might happen that two documents differ only in some names and numeric values. In this case they should not be considered same. This can be remedied by **augmenting this method with a Named Entity Recognizer and comparing the entities**.

## Trigram Results
As mentioned earlier, all trigrams do not appear in the real context. Here are the results of trigrams calculation on DEEP database different languages we tried:
### English
**Total english documents:** 22222

**Total size of the documents:** 413519133 Bytes ~ 413MB

**Trigrams Count(including numbers):** 19377 [Note that theoretically this would be around 50000]


### Spanish
**Total english documents:** 3333

**Total size of the documents:** 80739130 Bytes ~ 80MB

**Trigrams Count(including numbers):** 16265


### French
**Total english documents:** 755

**Total size of the documents:** 25650443 Bytes ~ 25MB

**Trigrams Count(including numbers):** 13391


## Resources
- [Near Duplicate Document Detection: Nice One](https://hal.inria.fr/hal-01542467/document)
- [Another nice one, uses genetic algorithm. Useful for overview of other methods in the literature review](https://www.researchgate.net/publication/328160386_A_Fast_Text_Similarity_Measure_for_Large_Document_Collections_using_Multi-reference_Cosine_and_Genetic_Algorithm)
- [Python Library that implements various algorithms for text similarity: **textdistance**](https://github.com/life4/textdistance)
