# This file is part of Linux Show Player
#
# Copyright 2022 Francesco Ceruti <ceppofrancy@gmail.com>
#
# Linux Show Player is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Linux Show Player is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Linux Show Player.  If not, see <http://www.gnu.org/licenses/>.

from abc import ABCMeta

from lisp.core.properties import Property, InstanceProperty
from lisp.core.signal import Signal
from lisp.core.util import typename


class HasPropertiesMeta(ABCMeta):
    """Metaclass for defining HasProperties classes.

    Use this metaclass to create an HasProperties. This metaclass takes care
    of keeping an update register of all the properties in the class and
    to propagate the changes in all the hierarchy.

    On it's own this metaclass it's not very useful, look at the HasProperty
    class for a comprehensive implementation.

    Note:
        This metaclass is derived form :class:`abc.ABCMeta`, so abstract
        classes can be created without using an intermediate metaclass
    """

    def __new__(mcls, name, bases, namespace, **kwargs):
        cls = super().__new__(mcls, name, bases, namespace, **kwargs)

        # Compute the set of property names
        cls._properties_ = {
            name
            for name, value in namespace.items()
            if isinstance(value, Property)
        }

        # Update the set from "proper" base classes
        for base in bases:
            if isinstance(base, HasPropertiesMeta):
                cls._properties_.update(base._properties_)

        return cls

    def __setattr__(cls, name, value):
        super().__setattr__(name, value)

        if isinstance(value, Property):
            cls._add_property(name)

    def __delattr__(cls, name):
        super().__delattr__(name)

        if name in cls._properties_:
            cls._del_property(name)

    def _add_property(cls, name):
        cls._properties_.add(name)
        for subclass in cls.__subclasses__():
            subclass._add_property(name)

    def _del_property(cls, name):
        cls._properties_.discard(name)
        for subclass in cls.__subclasses__():
            subclass._del_property(name)


class HasProperties(metaclass=HasPropertiesMeta):
    """Base class which allow to use Property and InstanceProperty.

    Using the Property descriptor subclasses can specify a set of properties
    that can be easily retrieved and updated via a series of provided functions.

    HasProperties objects can be nested, using a property that keeps an
    HasProperties object as a value.

    Usage:

        class DeepThought(HasProperties):
            the_answer = Property(default=42)
            nested = Property(default=AnotherThought.class_defaults())
    """

    def __init__(self):
        self.__changed_signals = {}
        # Contains signals that are emitted after the associated property is
        # changed, the signals are created only when requested the first time.

        self.property_changed = Signal()
        # Emitted after property change (self, name, value)

    def properties_names(self, filter=None):
        """
        To work as intended `filter` must be a function that takes a set as a
        parameter and return a set with the property names filtered by
        some custom rule. The given set can be modified in-place.

        :param filter: a function to filter the returned properties, or None
        :rtype: set
        :return: The object `Properties` names
        """
        if callable(filter):
            return filter(self._properties_names())
        else:
            return self._properties_names()

    def _properties_names(self):
        """Return a set of properties names, intended for internal usage.

        The returned set is a copy of the internal one, so it can be modified
        in-place.

        :rtype: set
        """
        return self.__class__._properties_.copy()

    def properties_defaults(self, filter=None):
        """Instance properties defaults.

        Different from `class_defaults` this works on instances, and it might
        give different results with some subclasses.

        :param filter: filter the properties, see `properties_names`
        :return: The default properties as a dictionary {name: default_value}
        :rtype: dict
        """
        defaults = {}

        for name in self.properties_names(filter=filter):
            value = self._property(name).default
            if isinstance(value, HasProperties):
                value = value.properties_defaults()

            defaults[name] = value

        return defaults

    @classmethod
    def class_defaults(cls, filter=None):
        """Class properties defaults.

        This function will not go into nested properties, the default
        value should already be set to a suitable value.

        :param filter: filter the properties, see `properties_names`
        :return: The default properties as a dictionary {name: default_value}
        :rtype: dict
        """
        if callable(filter):
            return {
                name: getattr(cls, name).default
                for name in filter(cls._properties_.copy())
            }
        else:
            return {
                name: getattr(cls, name).default for name in cls._properties_
            }

    def properties(self, defaults=True, filter=None):
        """
        :param filter: filter the properties, see `properties_names`
        :param defaults: include/exclude properties equals to their default
        :type defaults: bool

        :return: The properties as a dictionary {name: value}
        :rtype: dict
        """
        properties = {}

        for name in self.properties_names(filter=filter):
            value = getattr(self, name)

            if isinstance(value, HasProperties):
                value = value.properties(defaults=defaults, filter=filter)
                if defaults or value:
                    properties[name] = value
            elif defaults or value != self._property(name).default:
                properties[name] = value

        return properties

    def update_properties(self, properties):
        """Update the current properties using the given dict.

        :param properties: The element properties
        :type properties: dict
        """
        for name, value in properties.items():
            if name in self.properties_names():
                current = getattr(self, name)
                if isinstance(current, HasProperties):
                    current.update_properties(value)
                else:
                    # fix to avoid that some elements in "controller" (i.e. "osc","midi","keyboard") are lost when relative checkbox is not selected
                    #if name == "controller":   
                    #    for key in current.keys():
                    #        if key not in value:
                    #            value[key] = current[key]
                    setattr(self, name, value)

    def changed(self, name):
        """
        :param name: The property name
        :return: A signal that notifies that the given property has changed
        :rtype: Signal

        The signals returned by this method are created lazily and cached.
        """
        if name not in self.properties_names():
            raise ValueError(f'no property "{name}" found')

        signal = self.__changed_signals.get(name)
        if signal is None:
            signal = Signal()
            self.__changed_signals[name] = signal

        return signal

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name in self.properties_names():
            self._emit_changed(name, value)

    def _emit_changed(self, name, value):
        self.property_changed.emit(self, name, value)
        try:
            self.__changed_signals[name].emit(value)
        except KeyError:
            pass

    def _property(self, name):
        if name in self.__class__._properties_:
            return getattr(self.__class__, name)

        # TODO: PropertyError ??
        raise AttributeError(
            f"'{typename(self)}' object has no property '{name}'"
        )


class HasInstanceProperties(HasProperties):
    # Fallback __init__
    _i_properties_ = set()

    def __init__(self):
        super().__init__()
        self._i_properties_ = set()
        # Registry to keep track of instance-properties

    def _properties_names(self):
        return super()._properties_names().union(self._i_properties_)

    def __getattribute__(self, name):
        attribute = super().__getattribute__(name)
        if isinstance(attribute, InstanceProperty):
            return attribute.__pget__()

        return attribute

    def __setattr__(self, name, value):
        if isinstance(value, InstanceProperty):
            super().__setattr__(name, value)
            self._i_properties_.add(name)
        elif name in self._i_properties_:
            property = super().__getattribute__(name)
            property.__pset__(value)
            self._emit_changed(name, value)
        else:
            super().__setattr__(name, value)

    def __delattr__(self, name):
        super().__delattr__(name)
        self._i_properties_.discard(name)

    def _property(self, name):
        if name in self._i_properties_:
            return self._getattribute(name)

        return super()._property(name)
