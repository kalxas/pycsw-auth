###################################################################
#
# Authors: Tom Kralidis <tomkralidis@gmail.com>
#          Angelos Tzotsos <tzotsos@gmail.com>
#
# Copyright (c) 2026 Tom Kralidis
# Copyright (c) 2026 Angelos Tzotsos
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation
# files (the "Software"), to deal in the Software without
# restriction, including without limitation the rights to use,
# copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
###################################################################

from copy import deepcopy
import logging
import os

from flask import Flask, abort, jsonify, request
from pycsw.wsgi_flask import BLUEPRINT as pycsw_blueprint
from pycsw.ogc.api.util import render_j2_template, yaml_load
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pycsw_auth.models import Record, Scope

LOGGER = logging.getLogger(__name__)
MEDIA_TYPE = 'application/json'

APP = Flask(__name__, static_url_path='/static')
APP.url_map.strict_slashes = False
APP.register_blueprint(pycsw_blueprint, url_prefix='/')

ENGINE = create_engine(os.environ.get('SQLALCHEMY_DATABASE_URI'))
SESSION = sessionmaker(bind=ENGINE)

with open(os.environ.get('PYCSW_AUTH_OPENAPI')) as fh:
    OPENAPI_DOCUMENT = yaml_load(fh)

try:
    from flask_cors import CORS
    CORS(APP)
except ImportError:  # CORS needs to be handled by upstream server
    pass


@APP.route('/auth/openapi')
def openapi():

    if request.accept_mimetypes.best == 'application/json':
        return jsonify(OPENAPI_DOCUMENT)
    else:
        pycsw_blueprint_config = deepcopy(pycsw_blueprint.config)
        pycsw_blueprint_config['server']['url'] = os.environ.get('PYCSW_AUTH_URL')  # noqa
        return render_j2_template(
            pycsw_blueprint_config, 'openapi.html', OPENAPI_DOCUMENT)


@APP.route('/auth/records')
def records():

    session = SESSION()

    response = get_records(session)

    return jsonify(response)


@APP.route('/auth/records/<identifier>')
def record(identifier):

    session = SESSION()

    response = get_record(session, identifier)
    if response is None:
        abort(404, 'Record not found')

    if request.method == 'GET':
        return jsonify(response)


@APP.route('/auth/scopes', methods=['GET', 'POST'])
def scopes():

    session = SESSION()

    if request.method == 'GET':
        response = _get_scopes(session)
        return jsonify(response)
    elif request.method == 'POST':
        data = request.get_json()
        if data is None or not data:
            abort(400, 'Empty payload')

        response = _create_scope(session, data)

        return '', 201


@APP.route('/auth/scopes/<identifier>', methods=['GET', 'PUT', 'DELETE'])
def scope(identifier):

    session = SESSION()

    response = _get_scope(session, identifier)

    if response is None:
        abort(404, 'Record not found')

    if request.method == 'GET':
        return jsonify(response)
    elif request.method == 'PUT':
        data = request.get_json()
        if data is None or not data:
            abort(400, 'Empty payload')

        response = _update_scope(session, identifier, data)

        return '', 204
    elif request.method == 'DELETE':
        response = _delete_scope(session, identifier)
        return '', 204


def get_records(session):

    response = {
        'records': []
    }

    for record in session.query(Record).all():
        response['records'].append({
            'identifier': record.identifier,
            'scopes': [scope.identifier for scope in record.scopes]
        })

    return response


def get_record(session, identifier):

    response = None

    try:
        record = session.query(Record).filter_by(identifier=identifier).one()
        response = {
            'identifier': record.identifier,
            'scopes': [scope.identifier for scope in record.scopes]
        }
    except Exception as err:
        LOGGER.debug(err)

    return response


def _get_scopes(session):
    response = {
        'scopes': []
    }

    for scope in session.query(Scope).all():
        response['scopes'].append({
            'identifier': scope.identifier,
            'record_identifier': scope.record_identifier,
            'can_read': scope.can_read,
            'can_create': scope.can_create,
            'can_replace': scope.can_replace,
            'can_update': scope.can_update,
            'can_delete': scope.can_delete
        })

    return response


def _get_scope(session, identifier):

    response = None

    try:
        scope = session.query(Scope).filter_by(identifier=identifier).one()
        response = {
            'identifier': scope.identifier,
            'record_identifier': scope.record_identifier,
            'can_read': scope.can_read,
            'can_create': scope.can_create,
            'can_replace': scope.can_replace,
            'can_update': scope.can_update,
            'can_delete': scope.can_delete
        }
    except Exception as err:
        LOGGER.debug(err)

    return response


def _create_scope(session, data):

    record_identifier = data.get('record_identifier')
    record = session.query(Record).filter_by(
                 identifier=record_identifier).first()

    if not record:
        record = Record(identifier=record_identifier)
        session.add(record)

    scope = Scope(
        identifier=data.get('identifier'),
        can_create=data.get('can_create'),
        can_read=data.get('can_read'),
        can_replace=data.get('can_replace'),
        can_update=data.get('can_update'),
        can_delete=data.get('can_delete'),
        record=record
    )

    session.add(scope)
    session.commit()
    session.close()


def _update_scope(session, identifier, data):

    session.query(Scope).filter_by(identifier=identifier).update(**data)

    session.commit()
    session.close()


def _delete_scope(session, identifier):

    session.query(Scope).filter_by(identifier=identifier).delete()

    session.commit()
    session.close()
