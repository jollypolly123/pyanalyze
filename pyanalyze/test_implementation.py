# static analysis: ignore
from .test_name_check_visitor import TestNameCheckVisitorBase
from .test_node_visitor import assert_fails, assert_passes
from .error_code import ErrorCode
from .value import KnownValue, TypedValue, GenericValue


class TestSuperCall(TestNameCheckVisitorBase):
    @assert_passes()
    def test_basic(self):
        # there was a bug where we would insert the 'self' argument twice for super methods
        class Cachiyacuy(object):
            def eat_food(self):
                pass

        class Acouchy(Cachiyacuy):
            def do_it(self):
                return self.eat_food()

            def eat_food(self):
                super(Acouchy, self).eat_food()

    @assert_passes()
    def test_super_no_args(self):
        class Canaanimys:
            def __init__(self, a, b):
                super().__init__()

    @assert_fails(ErrorCode.incompatible_call)
    def test_super_no_args_wrong_args(self):
        class Gaudeamus:
            def eat(self):
                pass

        class Canaanimys(Gaudeamus):
            def eat(self, grass):
                super(Canaanimys, self).eat(grass)

    @assert_fails(ErrorCode.incompatible_call)
    def test_super_no_args_wrong_args_classmethod(self):
        class Gaudeamus:
            @classmethod
            def eat(cls):
                pass

        class Canaanimys(Gaudeamus):
            @classmethod
            def eat(cls, grass):
                super().eat(grass)

    @assert_fails(ErrorCode.bad_super_call)
    def test_super_no_args_in_comprehension(self):
        class Canaanimys:
            def __init__(self, a, b):
                self.x = [super().__init__() for _ in range(1)]

    @assert_fails(ErrorCode.bad_super_call)
    def test_super_no_args_in_gen_exp(self):
        class Canaanimys:
            def __init__(self, a, b):
                self.x = (super().__init__() for _ in range(1))

    @assert_fails(ErrorCode.bad_super_call)
    def test_super_no_args_in_nested_function(self):
        class Canaanimys:
            def __init__(self, a, b):
                def nested():
                    self.x = super().__init__()

                nested()

    @assert_passes()
    def test_super_init_subclass(self):
        class Pithanotomys:
            def __init_subclass__(self):
                super().__init_subclass__()

    @assert_passes()
    def test_good_super_call(self):
        from pyanalyze.tests import wrap, PropertyObject

        @wrap
        class Tainotherium(PropertyObject):
            def non_async_method(self):
                super(Tainotherium.base, self).non_async_method()

    @assert_fails(ErrorCode.bad_super_call)
    def test_bad_super_call(self):
        from pyanalyze.tests import wrap, PropertyObject

        @wrap
        class Tainotherium2(PropertyObject):
            def non_async_method(self):
                super(Tainotherium2, self).non_async_method()

    @assert_fails(ErrorCode.bad_super_call)
    def test_first_arg_is_base(self):
        class Base1(object):
            def method(self):
                pass

        class Base2(Base1):
            def method(self):
                pass

        class Child(Base2):
            def method(self):
                super(Base2, self).method()

    @assert_fails(ErrorCode.bad_super_call)
    def test_bad_super_call_classmethod(self):
        from pyanalyze.tests import wrap, PropertyObject

        @wrap
        class Tainotherium3(PropertyObject):
            @classmethod
            def no_args_classmethod(cls):
                super(Tainotherium3, cls).no_args_classmethod()

    @assert_fails(ErrorCode.incompatible_call)
    def test_super_attribute(self):
        class MotherCapybara(object):
            def __init__(self, grass):
                pass

        class ChildCapybara(MotherCapybara):
            def __init__(self):
                super(ChildCapybara, self).__init__()

    @assert_fails(ErrorCode.undefined_attribute)
    def test_undefined_super_attribute(self):
        class MotherCapybara(object):
            pass

        class ChildCapybara(MotherCapybara):
            @classmethod
            def toggle(cls):
                super(ChildCapybara, cls).toggle()

    @assert_passes()
    def test_metaclass(self):
        import six

        class CapybaraType(type):
            def __init__(self, name, bases, attrs):
                super(CapybaraType, self).__init__(name, bases, attrs)

        class Capybara(six.with_metaclass(CapybaraType)):
            pass

    @assert_passes()
    def test_mixin(self):
        class Base(object):
            @classmethod
            def eat(cls):
                pass

        class Mixin(object):
            @classmethod
            def eat(cls):
                super(Mixin, cls).eat()

        class Capybara(Mixin, Base):
            pass

    @assert_passes()
    def test_multi_valued(self):
        Capybara = 42

        class Capybara(object):
            pass

        C = Capybara

        def fn():
            assert_is_value(Capybara, MultiValuedValue([KnownValue(42), KnownValue(C)]))


class TestSequenceImpl(TestNameCheckVisitorBase):
    @assert_passes()
    def test(self):
        def capybara(x):
            # no arguments
            assert_is_value(set(), KnownValue(set()))
            assert_is_value(list(), KnownValue([]))

            # KnownValue
            assert_is_value(tuple([1, 2, 3]), KnownValue((1, 2, 3)))

            # Comprehensions
            one_two = MultiValuedValue([KnownValue(1), KnownValue(2)])
            assert_is_value(tuple(i for i in (1, 2)), GenericValue(tuple, [one_two]))
            assert_is_value(
                tuple({i: i for i in (1, 2)}), GenericValue(tuple, [one_two])
            )

            # SequenceIncompleteValue
            assert_is_value(
                tuple([int(x)]), SequenceIncompleteValue(tuple, [TypedValue(int)])
            )

            # fallback
            assert_is_value(tuple(x), TypedValue(tuple))

            # argument that is iterable but does not have __iter__
            assert_is_value(tuple(str(x)), TypedValue(tuple))

    @assert_fails(ErrorCode.unsupported_operation)
    def test_tuple_known_int(self):
        def capybara(x):
            tuple(3)

    @assert_fails(ErrorCode.unsupported_operation)
    def test_tuple_typed_int(self):
        def capybara(x):
            tuple(int(x))


class TestFormat(TestNameCheckVisitorBase):
    @assert_passes()
    def test_basic(self):
        def capybara():
            assert_is_value("{}".format(0), TypedValue(str))
            assert_is_value("{x}".format(x=0), TypedValue(str))
            assert_is_value("{} {x.imag!r:.2d}".format(0, x=0), TypedValue(str))
            assert_is_value("{x[0]} {y[x]}".format(x=[0], y={"x": 0}), TypedValue(str))
            assert_is_value("{{X}} {}".format(0), TypedValue(str))
            assert_is_value("{0:.{1:d}e}".format(0, 1), TypedValue(str))
            assert_is_value("{:<{width}}".format("", width=1), TypedValue(str))

    @assert_fails(ErrorCode.incompatible_call)
    def test_out_of_range_implicit(self):
        def capybara():
            "{} {}".format(0)

    @assert_fails(ErrorCode.incompatible_call)
    def test_out_of_range_numbered(self):
        def capybara():
            "{0} {1}".format(0)

    @assert_fails(ErrorCode.incompatible_call)
    def test_out_of_range_named(self):
        def capybara():
            "{x}".format(y=3)

    @assert_fails(ErrorCode.incompatible_call)
    def test_unused_numbered(self):
        def capybara():
            "{}".format(0, 1)

    @assert_fails(ErrorCode.incompatible_call)
    def test_unused_named(self):
        def capybara():
            "{x}".format(x=0, y=1)


class TestTypeMethods(TestNameCheckVisitorBase):
    @assert_passes()
    def test(self):
        class Capybara(object):
            def __init__(self, name):
                pass

            def foo(self):
                print(Capybara.__subclasses__())


class TestEncodeDecode(TestNameCheckVisitorBase):
    @assert_passes()
    def test(self):
        import six

        def capybara():
            assert_is_value(u"".encode("utf-8"), TypedValue(bytes))
            assert_is_value(b"".decode("utf-8"), TypedValue(six.text_type))

    @assert_fails(ErrorCode.incompatible_argument)
    def test_encode_wrong_type(self):
        def capybara():
            u"".encode(42)

    @assert_fails(ErrorCode.incompatible_argument)
    def test_decode_wrong_type(self):
        def capybara():
            b"".decode(42)


class TestLen(TestNameCheckVisitorBase):
    @assert_passes()
    def test(self):
        def capybara(x):
            assert_is_value(len("a"), TypedValue(int))
            assert_is_value(len(list(x)), TypedValue(int))

            # if we don't know the type, there should be no error
            len(x)

    @assert_fails(ErrorCode.incompatible_argument)
    def test_wrong_type(self):
        def capybara():
            len(3)


class TestSubclasses(TestNameCheckVisitorBase):
    @assert_passes()
    def test(self):
        class Parent:
            pass

        class Child(Parent):
            pass

        def capybara(typ: type):
            assert_is_value(
                typ.__subclasses__(), GenericValue(list, [TypedValue(type)])
            )
            assert_is_value(Parent.__subclasses__(), KnownValue([Child]))