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

import os

from sqlalchemy import Boolean, Column, ForeignKey, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

BASE = declarative_base()


class Record(BASE):
    __tablename__ = 'records'

    identifier = Column(String, primary_key=True)
    scopes = relationship('Scope', back_populates='record',
                          cascade='all, delete-orphan')


class Scope(BASE):
    __tablename__ = 'scopes'

    identifier = Column(String, primary_key=True)
    can_create = Column(Boolean, nullable=False, default=False)
    can_read = Column(Boolean, nullable=False, default=False)
    can_replace = Column(Boolean, nullable=False, default=False)
    can_update = Column(Boolean, nullable=False, default=False)
    can_delete = Column(Boolean, nullable=False, default=False)

    record_identifier = Column(String, ForeignKey('records.identifier',
                               ondelete='CASCADE'))

    record = relationship('Record', back_populates='scopes')


if __name__ == '__main__':
    engine = create_engine(os.environ.get('SQLALCHEMY_DATABASE_URI'))
    BASE.metadata.create_all(engine)
