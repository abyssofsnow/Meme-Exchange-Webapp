# Save a new meme and return the URL where the client can store the picture.
@app.route('/meme/save-meme', methods=['PUT'])
def save_meme():
    identity = get_identity()

    if identity == '':
        abort(403)
    if not request.is_json:
        abort(404)

    filename = request.json["filename"]
    content_type = request.json["contentType"]
    title = request.json["title"]

    if not (filename and content_type):
        # One of the fields was missing in the JSON request
        abort(404)

    # Get the url where the picture will be stored.
    picture_url = create_avatar_upload_url(filename, content_type)

    # Create the meme's key.
    incomplete_key = datastore_client.key('Meme')
    key = datastore_client.allocate_ids(incomplete_key, 1) #Johnny Johnny please give me an id.

    #Create the meme object in datastore.
    entity = datastore.Entity(key[0])
    entity.update({
        'title': title,
        'owner': identity,
        'picture_id': filename,
        'id': key[0].id
    })
    datastore_client.put(entity)


    return jsonify({"signedUrl": picture_url, "meme_id": key[0].id})

@app.route('/meme/upload-new', methods=['GET'])
def navigate_upload_meme():
    identity = get_identity()

    if(identity == ''):
        abort(404)

    return render_template('memeUpload.html', identity=identity)