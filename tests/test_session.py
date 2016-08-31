# Copyright 2016 ZEROFAIL
#
# This file is part of Goblin.
#
# Goblin is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Goblin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Goblin.  If not, see <http://www.gnu.org/licenses/>.

"""Functional sessions tests"""

import pytest

from goblin import element
from goblin.traversal import bindprop


class TestCreationApi:

    @pytest.mark.asyncio
    async def test_create_vertex(self, app, person_class):
        session = await app.session()
        jon = person_class()
        jon.name = 'jonathan'
        jon.age = 38
        leif = person_class()
        leif.name = 'leifur'
        leif.age = 28
        session.add(jon, leif)
        assert not hasattr(jon, 'id')
        assert not hasattr(leif, 'id')
        await session.flush()
        assert hasattr(jon, 'id')
        assert session.current[jon.id] is jon
        assert jon.name == 'jonathan'
        assert jon.age == 38
        assert hasattr(leif, 'id')
        assert session.current[leif.id] is leif
        assert leif.name == 'leifur'
        assert leif.age == 28
        await app.close()

    @pytest.mark.asyncio
    async def test_create_edge(self, app, person_class, place_class,
                               lives_in_class):
        session = await app.session()
        jon = person_class()
        jon.name = 'jonathan'
        jon.age = 38
        montreal = place_class()
        montreal.name = 'Montreal'
        lives_in = lives_in_class(jon, montreal)
        session.add(jon, montreal, lives_in)
        await session.flush()
        assert hasattr(lives_in, 'id')
        assert session.current[lives_in.id] is lives_in
        assert lives_in.source is jon
        assert lives_in.target is montreal
        assert lives_in.source.__label__ == 'person'
        assert lives_in.target.__label__ == 'place'
        await app.close()

    @pytest.mark.asyncio
    async def test_create_edge_no_source(self, app, lives_in, person):
        session = await app.session()
        lives_in.source = person
        with pytest.raises(Exception):
            await session.save(lives_in)
        await app.close()

    @pytest.mark.asyncio
    async def test_create_edge_no_target(self, app, lives_in, place):
        session = await app.session()
        lives_in.target = place
        with pytest.raises(Exception):
            await session.save(lives_in)
        await app.close()

    @pytest.mark.asyncio
    async def test_create_edge_no_source_target(self, app, lives_in):
        session = await app.session()
        with pytest.raises(Exception):
            await session.save(lives_in)
        await app.close()

    @pytest.mark.asyncio
    async def test_get_vertex(self, app, person_class):
        session = await app.session()
        jon = person_class()
        jon.name = 'jonathan'
        jon.age = 38
        await session.save(jon)
        jid = jon.id
        result = await session.get_vertex(jon)
        assert result.id == jid
        assert result is jon
        await app.close()

    @pytest.mark.asyncio
    async def test_get_edge(self, app, person_class, place_class,
                            lives_in_class):
        session = await app.session()
        jon = person_class()
        jon.name = 'jonathan'
        jon.age = 38
        montreal = place_class()
        montreal.name = 'Montreal'
        lives_in = lives_in_class(jon, montreal)
        session.add(jon, montreal, lives_in)
        await session.flush()
        lid = lives_in.id
        result = await session.get_edge(lives_in)
        assert result.id == lid
        assert result is lives_in
        await app.close()

    @pytest.mark.asyncio
    async def test_get_vertex_doesnt_exist(self, app, person):
        session = await app.session()
        person._id = 1000000000000000000000000000000000000000000000
        result = await session.get_vertex(person)
        assert not result
        await app.close()

    @pytest.mark.asyncio
    async def test_get_edge_doesnt_exist(self, app, knows, person_class):
        session = await app.session()
        jon = person_class()
        leif = person_class()
        works_with = knows
        works_with.source = jon
        works_with.target = leif
        works_with._id = 1000000000000000000000000000000000000000000000
        result = await session.get_edge(works_with)
        assert not result
        await app.close()

    @pytest.mark.asyncio
    async def test_remove_vertex(self, app, person):
        session = await app.session()
        person.name = 'dave'
        person.age = 35
        await session.save(person)
        result = await session.g.V(person.id).one_or_none()
        assert result is person
        rid = result.id
        await session.remove_vertex(person)
        result = await session.g.V(rid).one_or_none()
        assert not result
        await app.close()

    @pytest.mark.asyncio
    async def test_remove_edge(self, app, person_class, place_class,
                               lives_in_class):
        session = await app.session()
        jon = person_class()
        jon.name = 'jonathan'
        jon.age = 38
        montreal = place_class()
        montreal.name = 'Montreal'
        lives_in = lives_in_class(jon, montreal)
        session.add(jon, montreal, lives_in)
        await session.flush()
        result = await session.g.E(lives_in.id).one_or_none()
        assert result is lives_in
        rid = result.id
        await session.remove_edge(lives_in)
        result = await session.g.E(rid).one_or_none()
        assert not result
        await app.close()

    @pytest.mark.asyncio
    async def test_update_vertex(self, app, person):
        session = await app.session()
        person.name = 'dave'
        person.age = 35
        result = await session.save(person)
        assert result.name == 'dave'
        assert result.age == 35
        person.name = 'david'
        person.age = None
        result = await session.save(person)
        assert result is person
        assert result.name == 'david'
        assert not result.age
        await app.close()

    @pytest.mark.asyncio
    async def test_update_edge(self, app, person_class, knows):
        session = await app.session()
        dave = person_class()
        leif = person_class()
        knows.source = dave
        knows.target = leif
        knows.notes = 'online'
        session.add(dave, leif)
        await session.flush()
        result = await session.save(knows)
        assert knows.notes == 'online'
        knows.notes = None
        result = await session.save(knows)
        assert result is knows
        assert not result.notes
        await app.close()


class TestTraversalApi:

    @pytest.mark.asyncio
    async def test_traversal_source_generation(self, app, person_class,
                                               knows_class):
        session = await app.session()
        traversal = session.traversal(person_class)
        assert repr(traversal) == 'g.V().hasLabel("person")'
        traversal = session.traversal(knows_class)
        assert repr(traversal) == 'g.E().hasLabel("knows")'
        await app.close()


    @pytest.mark.asyncio
    async def test_all(self, app, person_class):
        session = await app.session()
        dave = person_class()
        leif = person_class()
        jon = person_class()
        session.add(dave, leif, jon)
        await session.flush()
        resp = await session.traversal(person_class).all()
        results = []
        async for msg in resp:
            assert isinstance(msg, person_class)
            results.append(msg)
        assert len(results) > 2
        await app.close()

    @pytest.mark.asyncio
    async def test_one_or_none_one(self, app, person_class):
        session = await app.session()
        dave = person_class()
        leif = person_class()
        jon = person_class()
        session.add(dave, leif, jon)
        await session.flush()
        resp = await session.traversal(person_class).one_or_none()
        assert isinstance(resp, person_class)
        await app.close()

    @pytest.mark.asyncio
    async def test_traversal_bindprop(self, app, person_class):
        session = await app.session()
        itziri = person_class()
        itziri.name = 'itziri'
        result1 = await session.save(itziri)
        bound_name = bindprop(person_class, 'name', 'itziri', binding='v1')
        p1 = await session.traversal(person_class).has(
        *bound_name).one_or_none()
        await app.close()

    @pytest.mark.asyncio
    async def test_one_or_none_none(self, app):
        session = await app.session()
        none = await session.g.V().hasLabel(
            'a very unlikey label').one_or_none()
        assert not none
        await app.close()

    @pytest.mark.asyncio
    async def test_vertex_deserialization(self, app, person_class):
        session = await app.session()
        resp = await session.g.addV('person').property(
            person_class.name, 'leif').property('place_of_birth', 'detroit').one_or_none()
        assert isinstance(resp, person_class)
        assert resp.name == 'leif'
        assert resp.place_of_birth == 'detroit'
        await app.close()

    @pytest.mark.asyncio
    async def test_edge_desialization(self, app, knows_class):
        session = await app.session()
        p1 = await session.g.addV('person').one_or_none()
        p2 = await session.g.addV('person').one_or_none()
        e1 = await session.g.V(p1.id).addE('knows').to(
        session.g.V(p2.id)).property(
            knows_class.notes, 'somehow').property(
            'how_long', 1).one_or_none()
        assert isinstance(e1, knows_class)
        assert e1.notes == 'somehow'
        assert e1.how_long == 1
        await app.close()

    @pytest.mark.asyncio
    async def test_unregistered_vertex_deserialization(self, app):
        session = await app.session()
        dave = await session.g.addV(
            'unregistered').property('name', 'dave').one_or_none()
        assert isinstance(dave, element.GenericVertex)
        assert dave.name == 'dave'
        assert dave.__label__ == 'unregistered'
        await app.close()

    @pytest.mark.asyncio
    async def test_unregistered_edge_desialization(self, app):
        session = await app.session()
        p1 = await session.g.addV('person').one_or_none()
        p2 = await session.g.addV('person').one_or_none()
        e1 = await session.g.V(p1.id).addE('unregistered').to(
        session.g.V(p2.id)).property('how_long', 1).one_or_none()
        assert isinstance(e1, element.GenericEdge)
        assert e1.how_long == 1
        assert e1.__label__ == 'unregistered'
        await app.close()

    @pytest.mark.asyncio
    async def test_property_deserialization(self, app):
        session = await app.session()
        p1 = await session.g.addV('person').property(
        'name', 'leif').one_or_none()
        name = await session.g.V(p1.id).properties('name').one_or_none()
        assert name['value'] == 'leif'
        assert name['label'] == 'name'
        await app.close()

    @pytest.mark.asyncio
    async def test_non_element_deserialization(self, app):
        session = await app.session()
        p1 = await session.g.addV('person').property(
        'name', 'leif').one_or_none()
        one = await session.g.V(p1.id).count().one_or_none()
        assert one == 1
        await app.close()
