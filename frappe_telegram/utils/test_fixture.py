import frappe


class TestFixture():
    """
    A simple and responsible Fixture Manager
    :param DEFAULT_DOCTYPE: The doctype that will be used as default
    :param dependent_fixtures: A list of classes that will be used as dependent fixtures
    :param fixtures: A dict of already generated fixtures
    :param duplicate: A flag to indicate if the fixture is already set up
    """

    def __init__(self):
        self.DEFAULT_DOCTYPE = None
        self.TESTER_USER = frappe.session.user
        self.dependent_fixtures = []
        self.fixtures = frappe._dict()
        self.duplicate = False

    def setUp(self, skip_fixtures=False, skip_dependencies=False):
        """
        Set up the fixtures. Fixture will not be duplicated if already set up.

        Args:
            skip_fixtures (bool): Skip the fixture creation
            skip_dependencies (bool): Skip the dependency creation

        Returns:
            None
        """

        if frappe.session.user != self.TESTER_USER:
            frappe.set_user(self.TESTER_USER)

        if self.isSetUp():
            self.duplicate = True
            og: TestFixture = self.get_locals_obj()[self.__class__.__name__]
            self.fixtures = getattr(og, "fixtures", frappe._dict())
            self._dependent_fixture_instances = getattr(
                og, "_dependent_fixture_instances", [])
            return
        if not skip_dependencies:
            self.make_dependencies()

        if not skip_fixtures:
            self.make_fixtures()
        self.get_locals_obj()[self.__class__.__name__] = self

    def make_dependencies(self):
        """
        Invokes setUp on dependent fixture classes
        """
        if not self.dependent_fixtures or not len(self.dependent_fixtures):
            return
        self._dependent_fixture_instances = []

        for d_class in self.dependent_fixtures:
            d = d_class()
            d.setUp()
            self._dependent_fixture_instances.append(d)

    def destroy_dependencies(self):
        """
        Invokes tearDown on dependent fixture classes
        """
        if not self.dependent_fixtures or not len(self.dependent_fixtures):
            return

        # Reverse teardown

        for i in range(len(getattr(self, "_dependent_fixture_instances", []))):
            d = self._dependent_fixture_instances[len(
                self._dependent_fixture_instances) - i - 1]
            d.tearDown()

        self._dependent_fixture_instances = []

    def get_dependencies(self, doctype):
        """
        Get documents of specific doctype that this fixture depends on
        """
        if not self._dependent_fixture_instances:
            return []

        for d in self._dependent_fixture_instances:
            if doctype in d.fixtures:
                return d.fixtures[doctype]

        return []

    def make_fixtures(self):
        """
        Please override this function to make your own make_fixture implementation
        And call self.add_document to keep track of the created fixtures for cleaning up later
        """
        pass

    def delete_fixtures(self):
        """
        Goes through each fixture generated and deletes it
        """
        for dt, docs in self.fixtures.items():
            meta = frappe.get_meta(dt)
            for doc in docs:
                if not frappe.db.exists(dt, doc.name) or doc is None:
                    continue

                doc.reload()
                if doc.docstatus == 1:
                    doc.docstatus = 2
                    doc.save(ignore_permissions=True)

                frappe.delete_doc(
                    dt,
                    doc.name,
                    force=not meta.is_submittable,
                    ignore_permissions=True
                )

        self.fixtures = frappe._dict()

    def __getitem__(self, doctype_idx):
        if isinstance(doctype_idx, int):
            if not self.DEFAULT_DOCTYPE:
                raise Exception("DEFAULT_DOCTYPE is not defined")
            return self.fixtures[self.DEFAULT_DOCTYPE][doctype_idx]

        return self.fixtures[doctype_idx]

    def __len__(self):
        if not self.DEFAULT_DOCTYPE:
            raise Exception("DEFAULT_DOCTYPE is not defined")

        return len(self.fixtures.get(self.DEFAULT_DOCTYPE, []))

    def tearDown(self):
        """
        Tear Down all generated fixtures
        """
        if frappe.session.user != self.TESTER_USER:
            frappe.set_user(self.TESTER_USER)

        if self.duplicate:
            self.fixtures = frappe._dict()
            self._dependent_fixture_instances = []
            self.duplicate = False
            return
        self.delete_fixtures()
        self.destroy_dependencies()
        self.get_locals_obj()[self.__class__.__name__] = None

    def add_document(self, doc):
        """
        Call this after creation of every fixture to keep track of it for deletion later
        """
        if doc.doctype not in self.fixtures:
            self.fixtures[doc.doctype] = []

        self.fixtures[doc.doctype].append(doc)

    def isSetUp(self):
        """
        Checks if another instance of the same fixture class is already set up
        """
        class_name = self.__class__.__name__
        return not not self.get_locals_obj().get(class_name, 0)

    def get_locals_obj(self):
        if "test_fixtures" not in frappe.flags:
            frappe.flags.test_fixtures = frappe._dict()

        return frappe.flags.test_fixtures
