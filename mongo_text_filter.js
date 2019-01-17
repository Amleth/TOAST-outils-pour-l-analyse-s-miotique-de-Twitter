conn = new Mongo();
db = conn.getDB("si90");
db.si90_filtered.drop();
db.si90.ensureIndex({
  "raw.text": "text"
});

c = db.si90.aggregate([{
    $match: {
      $or: [{
          "raw.text": /ceci/gim
        },
        {
          "raw.text": /cela/gim
        }
      ]
    }
  },
  {
    $out: "si90_filtered"
  }
]);

while (c.hasNext()) {
  print(tojson(c.next()));
}

print(db.si90_filtered.find().count());