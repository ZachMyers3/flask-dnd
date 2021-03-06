from flask import Blueprint, abort, jsonify, request
from bson.objectid import ObjectId
import math

from ..models import mongo

from ..scripts.character_calc import calc_skill_mods

character = Blueprint('character', __name__)

API_STUB = '/api/v1'

@character.route(f'{API_STUB}/character', methods=['GET'])
def get_character():
    _id = request.args.get('_id', default=None, type=str)
    if not _id:
        return jsonify(ok=False, msg='_id field required'), 400
    this_char = mongo.db.characters.find_one({'_id': ObjectId(_id)})
    if this_char:
        return jsonify(ok=True, character=this_char)
    else:
        return jsonify(ok=False, msg='Character not found'), 404

@character.route(f'{API_STUB}/character', methods=['POST'])
def create_character():
    # TODO: verify player doesnt exist
    # go to characters store
    characters = mongo.db.characters
    # insert request
    pid = characters.insert(request.json)
    # find new player
    new_char = characters.find_one({'_id': pid})
    return jsonify(ok=True, character=new_char)

@character.route(f'{API_STUB}/character', methods=['PUT'])
def update_character():
    _id = ObjectId(request.json['_id'])
    if not request.json:
        return jsonify(ok=False, msg='JSON format required'), 400
    if not _id:
        return jsonify(ok=False, msg='ID is required to update'), 400
    # find the object by id and update from the rest of the json
    # update_json = {'_id': _id, '$set': request.json}
    request.json.pop('_id', None)
    mongo.db.characters.update_one({'_id': _id}, {'$set': request.json})
    this_char = mongo.db.characters.find_one({'_id': _id})

    return jsonify(ok=True, character=this_char)

@character.route(f'{API_STUB}/characters', methods=['GET'])
def get_characters():
    # get all characters (return a max per_page)
    results = list(mongo.db.characters.find())

    return jsonify(ok=True, characters=results)

@character.route(f'{API_STUB}/character', methods=['DELETE'])
def delete_character():
    _id = request.args.get('_id', default=None, type=str)
    if not _id:
        return jsonify(ok=False, msg='_id field required'), 400
    del_char = mongo.db.characters.find_one({'_id': ObjectId(_id)})
    if not del_char:
        return jsonify(ok=False, msg='Character not found'), 404
    del_result = mongo.db.characters.delete_one({'_id': ObjectId(_id)})
    if del_result:
        return jsonify(ok=True, character=del_char)


@character.route(f'{API_STUB}/character/learn_spell', methods=['PUT'])
def mark_spell_learned():
    # need character id, spell id
    try:
        char_id = ObjectId(request.args.get('_id', default=None, type=str))
    except:
        return jsonify(ok=False, msg='Invalid id format')
    spell_id = request.args.get('spell_id', default=None, type=int)
    if not char_id or not spell_id:
        return jsonify(ok=False, msg='_id and spell_id required')
    # verify the given character and spell can be found
    char = mongo.db.characters.find_one({'_id': char_id})
    # assign the found spell if its in the learnable spell list
    spell_to_learn = None
    for spell in char["spells"]:
        if spell["id"] == spell_id:
            spell_to_learn = spell
            break
    if not spell_to_learn:
        return jsonify(ok=False, msg='Cannot find given spell by id {spell_id}'), 404
    # set the learned attribute to the opposite of it's current value
    try:
        learned_status = spell_to_learn["learned"]
    except:
        learned_status = False
    # flip current status
    learned_status = not learned_status
    spell_to_learn["learned"] = learned_status

    mongo.db.characters.update_one({'_id': char_id}, {'$set': char})
    return jsonify(ok=True, data=char)

    