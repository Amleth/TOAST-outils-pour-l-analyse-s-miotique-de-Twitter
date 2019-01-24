conn = new Mongo()
db = conn.getDB('si90')
db.si90_filtered.drop()
db.si90.ensureIndex({
  'fulltext': 'text'
})

c = db.si90.aggregate([
  {
    $match: {
      $or: [
        {
          'fulltext': /#tralala/gim
        },
        {
          'fulltext': /cela/gim
        }
      ]
    }
  },
  {
    $out: 'si90_filtered'
  }
])

while (c.hasNext()) {
  print(tojson(c.next()))
}

print(db.si90_filtered.find().count())
