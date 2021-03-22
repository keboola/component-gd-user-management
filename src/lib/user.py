class User:
    """
    A class representing user in the whole MUF process.
    """
    def __init__(self, login, role, muf, action, first_name, last_name, sso_provider=None):

        """
        Init function.

        Parameters
        ----------
        login : str
            A login of the user.
        role : str
            A role of the user in the project.
        muf : str
            A data permission for the user.
        action : str
            A type of action to be performed with the user.
        first_name : str
            A first name of the user.
        last_name : str
            A last name of the user.
        """

        self.login = login
        self.role = role
        self.muf = muf
        self.action = action
        self.first_name = first_name
        self.last_name = last_name
        self.sso_provider = sso_provider
