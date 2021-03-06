import unittest
from zExceptions import Redirect


class TestOpenIdExtraction(unittest.TestCase):
    identity = "http://plone.myopenid.com"
    server_response={
            "openid.mode"              : "id_res",
            "nonce"                    : "nonce",
            "openid.identity"          : "http://plone.myopenid.com",
            "openid.assoc_handle"      : "assoc_handle",
            "openid.return_to"         : "return_to",
            "openid.signed"            : "signed",
            "openid.sig"               : "sig",
            "openid.invalidate_handle" : "invalidate_handle",
            }

    def createPlugin(self):
        from plone.openid.tests.utils import MockPAS
        from plone.openid.tests.utils import MockSite
        from plone.openid.plugins.oid import OpenIdPlugin
        plugin=OpenIdPlugin("openid")
        return plugin.__of__((MockPAS()).__of__(MockSite()))


    def testEmptyExtraction(self):
        """Test if we do not invent credentials out of thin air.
        """
        plugin=self.createPlugin()
        creds=plugin.extractCredentials(plugin.REQUEST)
        self.assertEqual(creds, {})


    def testEmptyStringIdentityExtraction(self):
        """Test coverage for bug #7176. In the case where "" (i.e an empty
           string) is passed in as the identity via the request,
           we essentially want to ensure that a Redirect isn't raised, which
           would signify that an IOpenIdExtractionPlugin challenge was initialized.

           This test demonstrates our openid plugin's extractCredentials eliminates
           credentials that aren't in the openid.* namespace.
        """
        plugin=self.createPlugin()
        plugin.REQUEST.form.update(self.server_response)
        plugin.REQUEST.form["__ac_identity_url"]=""
        creds=plugin.extractCredentials(plugin.REQUEST)
        self.failIf(creds.has_key("__ac_identity_url"))


    def testRedirect(self):
        """Test if a redirect is generated for a login attempt.
        This test requires a working internet connection!
        """
        plugin=self.createPlugin()
        plugin.REQUEST.form["__ac_identity_url"]=self.identity
        self.assertRaises(Redirect,
                plugin.extractCredentials,
                plugin.REQUEST)


    def testPositiveOpenIdResponse(self):
        """Test if a positive authentication is extracted.
        """
        plugin=self.createPlugin()
        plugin.REQUEST.form.update(self.server_response)
        creds=plugin.extractCredentials(plugin.REQUEST)
        self.assertEqual(creds["openid.identity"], self.identity)
        self.assertEqual(creds["openid.mode"], "id_res")
        self.assertEqual(creds["openid.return_to"], "return_to")


    def testNegativeOpenIdResponse(self):
        """Check if a cancelled authentication request is correctly ignored.
        """
        plugin=self.createPlugin()
        plugin.REQUEST.form.update(self.server_response)
        plugin.REQUEST.form["openid.mode"]="cancel"
        creds=plugin.extractCredentials(plugin.REQUEST)
        self.assertEqual(creds, {})


    def testFormRedirectPriorities(self):
        """Check if a new login identity has preference over openid server
        reponse.
        """
        plugin=self.createPlugin()
        plugin.REQUEST.form.update(self.server_response)
        plugin.REQUEST.form["__ac_identity_url"]=self.identity
        self.assertRaises(Redirect,
                plugin.extractCredentials, plugin.REQUEST)

    def testUnallowedOpenIDProviderExtraction(self):
        """Check that redirect is not raised when we try to login with
        unallowed openid provider url.
        """
        plugin=self.createPlugin()
        setattr(plugin, 'allowed_openid_providers', [self.identity])
        plugin.REQUEST.form.update(self.server_response)
        plugin.REQUEST.form["__ac_identity_url"]="http://plone.mywrongopenid.com"

        creds=plugin.extractCredentials(plugin.REQUEST)
        self.failIf(creds.has_key("__ac_identity_url"))

    def testAllowedOpenIDProviderExtraction(self):
        """Check that we're redirected when we try to login with allowed
        openid provider url set in both openid properties and as login url.
        """
        plugin=self.createPlugin()
        setattr(plugin, 'allowed_openid_providers', [self.identity])
        plugin.REQUEST.form.update(self.server_response)
        plugin.REQUEST.form["__ac_identity_url"]=self.identity
        self.assertRaises(Redirect,
                plugin.extractCredentials, plugin.REQUEST)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite=TestSuite()
    suite.addTest(makeSuite(TestOpenIdExtraction))
    return suite
