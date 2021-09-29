VERSION=$1
LANG=$2

mkdir -p ../dumps/

echo "Download ${LANG}wiki-${VERSION}-pages-articles.xml.bz2"
curl https://dumps.wikimedia.org/${LANG}wiki/${VERSION}/${LANG}wiki-${VERSION}-pages-articles.xml.bz2 \
--output ../dumps/${LANG}wiki-${VERSION}-pages-articles.xml.bz2