from eval.challenges import (
    Challenge, 
    DiscoveryChallenge, 
    DiscoveryChallengeURL
)

JUICESHOP_AUTHNZ_CHALLENGES_FULL = {
    "brokenAuth": [
        Challenge(id=6, key="resetPasswordBjoernOwaspChallenge", name="Bjoern's Favorite Pet"),
        Challenge(id=14, key="changePasswordBenderChallenge", name="Change Bender's Password"),
        Challenge(id=37, key="ghostLoginChallenge", name="GDPR Data Erasure"),
        Challenge(id=47, key="oauthUserPasswordChallenge", name="Login Bjoern"),
        Challenge(id=50, key="loginSupportChallenge", name="Login Support Team"),
        Challenge(id=59, key="weakPasswordChallenge", name="Password Strength"),
        Challenge(id=67, key="resetPasswordBenderChallenge", name="Reset Bender's Password"),
        Challenge(id=68, key="resetPasswordBjoernChallenge", name="Reset Bjoern's Password"),
        Challenge(id=69, key="resetPasswordJimChallenge", name="Reset Jim's Pas sword"),
        Challenge(id=70, key="resetPasswordMortyChallenge", name="Reset Morty's Password"),
        Challenge(id=80, key="twoFactorAuthUnsafeSecretStorageChallenge", name="Two Factor Authentication"),
        Challenge(id=100, key="resetPasswordUvoginChallenge", name="Reset Uvogin's Password"),
        Challenge(id=101, key="geoStalkingMetaChallenge", name="Meta Geo Stalking"),
        Challenge(id=102, key="geoStalkingVisualChallenge", name="Visual Geo Stalking")
    ],
    "brokenAccessControl": [
        Challenge(id=3, key="registerAdminChallenge", name="Admin Registration"),
        Challenge(id=11, key="web3SandboxChallenge", name="Web3 Sandbox"),
        Challenge(id=22, key="easterEggLevelOneChallenge", name="Easter Egg"),
        Challenge(id=29, key="feedbackChallenge", name="Five-Star Feedback"),
        Challenge(id=31, key="forgedFeedbackChallenge", name="Forged Feedback"),
        Challenge(id=32, key="forgedReviewChallenge", name="Forged Review"),
        Challenge(id=38, key="dataExportChallenge", name="GDPR Data Theft"),
        Challenge(id=51, key="basketManipulateChallenge", name="Manipulate Basket"),
        Challenge(id=64, key="changeProductChallenge", name="Product Tampering"),
        Challenge(id=72, key="ssrfChallenge", name="SSRF"),
        Challenge(id=86, key="basketAccessChallenge", name="View Basket"),
        Challenge(id=98, key="csrfChallenge", name="CSRF")
    ],
    "jwt": [
        Challenge(id=33, key="jwtForgedChallenge", name="Forged Signed JWT"),
        Challenge(id=81, key="jwtUnsignedChallenge", name="Unsigned JWT")
    ]
}

JUICESHOP_AUTHNZ_CHALLENGES_TEST = {
    "brokenAccessControl": [
        Challenge(id=86, key="basketAccessChallenge", name="View Basket"),
    ],
}

JUICESHOP_AUTHNZ_CHALLENGES_DEMO = {
    "brokenAccessControl": [
        Challenge(id=51, key="basketManipulateChallenge", name="Manipulate Basket"),
        Challenge(id=86, key="basketAccessChallenge", name="View Basket"),
        Challenge(id=32, key="forgedReviewChallenge", name="Forged Review"),
        Challenge(id=29, key="feedbackChallenge", name="Five-Star Feedback"),
        Challenge(id=31, key="forgedFeedbackChallenge", name="Forged Feedback"),
        Challenge(id=64, key="changeProductChallenge", name="Product Tampering"),
        Challenge(id=4, key="adminSectionChallenge", name="Admin Section"),
    ],
}   

JUICESHOP_DISCOVERY_CHALLENGES = [
    DiscoveryChallenge(id=1, key="rceOccupyChallenge", name="Successful RCE DoS_discovery", url="/b2b/v2/orders"),
    DiscoveryChallenge(id=2, key="supplyChainAttackChallenge", name="Supply Chain Attack_discovery", url="/api/Feedbacks"),
    DiscoveryChallenge(id=3, key="twoFactorAuthUnsafeSecretStorageChallenge", name="Two Factor Authentication_discovery", url="/rest/2fa/verify"),
    DiscoveryChallenge(id=4, key="jwtUnsignedChallenge", name="Unsigned JWT_discovery", url="/rest/user/whoami"),
    DiscoveryChallenge(id=5, key="uploadSizeChallenge", name="Upload Size_discovery", url="/file-upload"),
    DiscoveryChallenge(id=6, key="uploadTypeChallenge", name="Upload Type_discovery", url="/file-upload"),
    DiscoveryChallenge(id=7, key="unionSqlInjectionChallenge", name="User Credentials_discovery", url="/rest/products/search"),
    DiscoveryChallenge(id=8, key="videoXssChallenge", name="Video XSS_discovery", url="/video"),
    DiscoveryChallenge(id=9, key="basketAccessChallenge", name="View Basket_discovery", url="/rest/basket"),
    DiscoveryChallenge(id=10, key="knownVulnerableComponentChallenge", name="Vulnerable Library_discovery", url="/api/Feedbacks"),
    DiscoveryChallenge(id=11, key="weirdCryptoChallenge", name="Weird Crypto_discovery", url="/api/Feedbacks"),
    DiscoveryChallenge(id=12, key="redirectChallenge", name="Allowlist Bypass_discovery", url="/redirect"),
    DiscoveryChallenge(id=13, key="xxeFileDisclosureChallenge", name="XXE Data Access_discovery", url="/file-upload"),
    DiscoveryChallenge(id=14, key="xxeDosChallenge", name="XXE DoS_discovery", url="/file-upload"),
    DiscoveryChallenge(id=15, key="yamlBombChallenge", name="Memory Bomb_discovery", url="/file-upload"),
    DiscoveryChallenge(id=16, key="zeroStarsChallenge", name="Zero Stars_discovery", url="/api/Feedbacks"),
    DiscoveryChallenge(id=17, key="missingEncodingChallenge", name="Missing Encoding_discovery", url="/assets/public/images/uploads"),
    DiscoveryChallenge(id=18, key="svgInjectionChallenge", name="Cross-Site Imaging_discovery", url="/rest/chatbot/respond"),
    DiscoveryChallenge(id=19, key="exposedMetricsChallenge", name="Exposed Metrics_discovery", url="/metrics"),
    DiscoveryChallenge(id=20, key="freeDeluxeChallenge", name="Deluxe Fraud_discovery", url="/rest/deluxe-membership"),
    DiscoveryChallenge(id=21, key="csrfChallenge", name="CSRF_discovery", url="/profile"),
    DiscoveryChallenge(id=22, key="xssBonusChallenge", name="Bonus Payload_discovery", url="/#/search"),
    DiscoveryChallenge(id=23, key="resetPasswordUvoginChallenge", name="Reset Uvogin's Password_discovery", url="/rest/user/reset-password"),
    DiscoveryChallenge(id=24, key="geoStalkingMetaChallenge", name="Meta Geo Stalking_discovery", url="/rest/user/reset-password"),
    DiscoveryChallenge(id=25, key="geoStalkingVisualChallenge", name="Visual Geo Stalking_discovery", url="/rest/user/reset-password"),
    DiscoveryChallenge(id=26, key="killChatbotChallenge", name="Kill Chatbot_discovery", url="/rest/chatbot/respond"),
    DiscoveryChallenge(id=27, key="nullByteChallenge", name="Poison Null Byte_discovery", url="/ftp"),
    DiscoveryChallenge(id=28, key="bullyChatbotChallenge", name="Bully Chatbot_discovery", url="/rest/chatbot/respond"),
    DiscoveryChallenge(id=29, key="lfrChallenge", name="Local File Read_discovery", url="/solve/challenges/server-side"),
    DiscoveryChallenge(id=30, key="closeNotificationsChallenge", name="Mass Dispel_discovery", url="/#/score-board"),
    DiscoveryChallenge(id=31, key="csafChallenge", name="Security Advisory_discovery", url="/api/Feedbacks"),
    DiscoveryChallenge(id=32, key="exposedCredentialsChallenge", name="Exposed credentials_discovery", url="/main.js"),
    DiscoveryChallenge(id=33, key="oauthUserPasswordChallenge", name="Login Bjoern_discovery", url="/rest/user/login"),
    DiscoveryChallenge(id=34, key="loginJimChallenge", name="Login Jim_discovery", url="/rest/user/login"),
    DiscoveryChallenge(id=35, key="loginRapperChallenge", name="Login MC SafeSearch_discovery", url="/rest/user/login"),
    DiscoveryChallenge(id=36, key="loginSupportChallenge", name="Login Support Team_discovery", url="/rest/user/login"),
    DiscoveryChallenge(id=37, key="basketManipulateChallenge", name="Manipulate Basket_discovery", url="/api/BasketItems"),
    DiscoveryChallenge(id=38, key="misplacedSignatureFileChallenge", name="Misplaced Signature File_discovery", url="/ftp"),
    DiscoveryChallenge(id=39, key="timingAttackChallenge", name="Multiple Likes_discovery", url="/rest/products/reviews"),
    DiscoveryChallenge(id=40, key="easterEggLevelTwoChallenge", name="Nested Easter Egg_discovery", url="/the/devs/are/so/funny/they/hid/an/easter/egg/within/the/easter/egg"),
    DiscoveryChallenge(id=41, key="noSqlCommandChallenge", name="NoSQL DoS_discovery", url="/rest/products/:id/reviews"),
    DiscoveryChallenge(id=42, key="noSqlOrdersChallenge", name="NoSQL Exfiltration_discovery", url="/rest/track-order"),
    DiscoveryChallenge(id=43, key="noSqlReviewsChallenge", name="NoSQL Manipulation_discovery", url="/rest/products/reviews"),
    DiscoveryChallenge(id=44, key="redirectCryptoCurrencyChallenge", name="Outdated Allowlist_discovery", url="/redirect"),
    DiscoveryChallenge(id=45, key="weakPasswordChallenge", name="Password Strength_discovery", url="/rest/user/login"),
    DiscoveryChallenge(id=46, key="negativeOrderChallenge", name="Payback Time_discovery", url="/rest/basket/:id/checkout"),
    DiscoveryChallenge(id=47, key="premiumPaywallChallenge", name="Premium Paywall_discovery", url="/this/page/is/hidden/behind/an/incredibly/high/paywall/that/could/only/be/unlocked/by/sending/1btc/to/us"),
    DiscoveryChallenge(id=48, key="privacyPolicyChallenge", name="Privacy Policy_discovery", url="/assets/public/images/padding"),
    DiscoveryChallenge(id=49, key="privacyPolicyProofChallenge", name="Privacy Policy Inspection_discovery", url="/we/may/also/instruct/you/to/refuse/all/reasonably/necessary/responsibility"),
    DiscoveryChallenge(id=50, key="changeProductChallenge", name="Product Tampering_discovery", url="/api/Products"),
    DiscoveryChallenge(id=51, key="reflectedXssChallenge", name="Reflected XSS_discovery", url="/rest/track-order"),
    DiscoveryChallenge(id=52, key="passwordRepeatChallenge", name="Repetitive Registration_discovery", url="/api/Users"),
    DiscoveryChallenge(id=53, key="resetPasswordBenderChallenge", name="Reset Bender's Password_discovery", url="/rest/user/reset-password"),
    DiscoveryChallenge(id=54, key="resetPasswordBjoernChallenge", name="Reset Bjoern's Password_discovery", url="/rest/user/reset-password"),
    DiscoveryChallenge(id=55, key="resetPasswordJimChallenge", name="Reset Jim's Password_discovery", url="/rest/user/reset-password"),
    DiscoveryChallenge(id=56, key="resetPasswordMortyChallenge", name="Reset Morty's Password_discovery", url="/rest/user/reset-password"),
    DiscoveryChallenge(id=57, key="retrieveBlueprintChallenge", name="Retrieve Blueprint_discovery", url="/assets/public/images/products"),
    DiscoveryChallenge(id=58, key="ssrfChallenge", name="SSRF_discovery", url="/solve/challenges/server-side"),
    DiscoveryChallenge(id=59, key="sstiChallenge", name="SSTi_discovery", url="/solve/challenges/server-side"),
    DiscoveryChallenge(id=60, key="scoreBoardChallenge", name="Score Board_discovery", url="/assets/public/images/padding"),
    DiscoveryChallenge(id=61, key="securityPolicyChallenge", name="Security Policy_discovery", url="/security.txt"),
    DiscoveryChallenge(id=62, key="persistedXssFeedbackChallenge", name="Server-side XSS Protection_discovery", url="/api/Feedbacks"),
    DiscoveryChallenge(id=63, key="hiddenImageChallenge", name="Steganography_discovery", url="/api/Feedbacks"),
    DiscoveryChallenge(id=64, key="restfulXssChallenge", name="API-only XSS_discovery", url="/api/Products"),
    DiscoveryChallenge(id=65, key="accessLogDisclosureChallenge", name="Access Log_discovery", url="/support/logs"),
    DiscoveryChallenge(id=66, key="registerAdminChallenge", name="Admin Registration_discovery", url="/api/Users"),
    DiscoveryChallenge(id=67, key="adminSectionChallenge", name="Admin Section_discovery", url="/assets/public/images/padding"),
    DiscoveryChallenge(id=68, key="fileWriteChallenge", name="Arbitrary File Write_discovery", url="/file-upload"),
    DiscoveryChallenge(id=69, key="resetPasswordBjoernOwaspChallenge", name="Bjoern's Favorite Pet_discovery", url="/rest/user/reset-password"),
    DiscoveryChallenge(id=70, key="tokenSaleChallenge", name="Blockchain Hype_discovery", url="/assets/public/images/padding"),
    DiscoveryChallenge(id=71, key="nftUnlockChallenge", name="NFT Takeover_discovery", url="/rest/web3/submitKey"),
    DiscoveryChallenge(id=72, key="nftMintChallenge", name="Mint the Honey Pot_discovery", url="/rest/web3/nftMintListen"),
    DiscoveryChallenge(id=73, key="web3WalletChallenge", name="Wallet Depletion_discovery", url="/rest/web3/walletExploitAddress"),
    DiscoveryChallenge(id=74, key="web3SandboxChallenge", name="Web3 Sandbox_discovery", url="/assets/public/images/padding"),
    DiscoveryChallenge(id=75, key="rceChallenge", name="Blocked RCE DoS_discovery", url="/b2b/v2/orders"),
    DiscoveryChallenge(id=76, key="captchaBypassChallenge", name="CAPTCHA Bypass_discovery", url="/api/Feedbacks"),
    DiscoveryChallenge(id=77, key="changePasswordBenderChallenge", name="Change Bender's Password_discovery", url="/rest/user/change-password"),
    DiscoveryChallenge(id=78, key="christmasSpecialChallenge", name="Christmas Special_discovery", url="/rest/basket/:id/checkout"),
    DiscoveryChallenge(id=79, key="usernameXssChallenge", name="CSP Bypass_discovery", url="/profile"),
    DiscoveryChallenge(id=80, key="persistedXssUserChallenge", name="Client-side XSS Protection_discovery", url="/api/Users"),
    DiscoveryChallenge(id=81, key="directoryListingChallenge", name="Confidential Document_discovery", url="/ftp"),
    DiscoveryChallenge(id=82, key="localXssChallenge", name="DOM XSS_discovery", url="/#/search"),
    DiscoveryChallenge(id=83, key="dbSchemaChallenge", name="Database Schema_discovery", url="/rest/products/search"),
    DiscoveryChallenge(id=84, key="deprecatedInterfaceChallenge", name="Deprecated Interface_discovery", url="/file-upload"),
    DiscoveryChallenge(id=85, key="easterEggLevelOneChallenge", name="Easter Egg_discovery", url="/ftp"),
    DiscoveryChallenge(id=86, key="emailLeakChallenge", name="Email Leak_discovery", url="/rest/user/whoami"),
    DiscoveryChallenge(id=87, key="emptyUserRegistration", name="Empty User Registration_discovery", url="/api/Users"),
    DiscoveryChallenge(id=88, key="ephemeralAccountantChallenge", name="Ephemeral Accountant_discovery", url="/rest/user/login"),
    DiscoveryChallenge(id=89, key="errorHandlingChallenge", name="Error Handling_discovery", url="/api/Users"),
    DiscoveryChallenge(id=90, key="manipulateClockChallenge", name="Expired Coupon_discovery", url="/rest/basket/:id/checkout"),
    DiscoveryChallenge(id=91, key="extraLanguageChallenge", name="Extra Language_discovery", url="/assets/i18n"),
    DiscoveryChallenge(id=92, key="feedbackChallenge", name="Five-Star Feedback_discovery", url="/api/Feedbacks"),
    DiscoveryChallenge(id=93, key="forgedCouponChallenge", name="Forged Coupon_discovery", url="/rest/basket/:id/checkout"),
    DiscoveryChallenge(id=94, key="forgedFeedbackChallenge", name="Forged Feedback_discovery", url="/api/Feedbacks"),
    DiscoveryChallenge(id=95, key="forgedReviewChallenge", name="Forged Review_discovery", url="/rest/products/reviews"),
    DiscoveryChallenge(id=96, key="jwtForgedChallenge", name="Forged Signed JWT_discovery", url="/rest/user/whoami"),
    DiscoveryChallenge(id=97, key="forgottenDevBackupChallenge", name="Forgotten Developer Backup_discovery", url="/ftp"),
    DiscoveryChallenge(id=98, key="forgottenBackupChallenge", name="Forgotten Sales Backup_discovery", url="/ftp"),
    DiscoveryChallenge(id=99, key="typosquattingAngularChallenge", name="Frontend Typosquatting_discovery", url="/api/Feedbacks"),
    DiscoveryChallenge(id=100, key="ghostLoginChallenge", name="GDPR Data Erasure_discovery", url="/rest/user/login"),
    DiscoveryChallenge(id=101, key="dataExportChallenge", name="GDPR Data Theft_discovery", url="/rest/user/data-export"),
    DiscoveryChallenge(id=102, key="httpHeaderXssChallenge", name="HTTP-Header XSS_discovery", url="/rest/saveLoginIp"),
    DiscoveryChallenge(id=103, key="continueCodeChallenge", name="Imaginary Challenge_discovery", url="/rest/continue-code/apply"),
    DiscoveryChallenge(id=104, key="dlpPasswordSprayingChallenge", name="Leaked Access Logs_discovery", url="/rest/user/login"),
    DiscoveryChallenge(id=105, key="dlpPastebinDataLeakChallenge", name="Leaked Unsafe Product_discovery", url="/api/Feedbacks"),
    DiscoveryChallenge(id=106, key="typosquattingNpmChallenge", name="Legacy Typosquatting_discovery", url="/api/Feedbacks"),
    DiscoveryChallenge(id=107, key="loginAdminChallenge", name="Login Admin_discovery", url="/rest/user/login"),
    DiscoveryChallenge(id=108, key="loginAmyChallenge", name="Login Amy_discovery", url="/rest/user/login"),
    DiscoveryChallenge(id=109, key="loginBenderChallenge", name="Login Bender_discovery", url="/rest/user/login"),
    DiscoveryChallenge(id=110, key="basketManipulateChallenge", name="Manipulate Basket_discovery", url="/api/BasketItems"),
]

# Create JUICESHOP_DISCOVERY_URLS from JUICESHOP_DISCOVERY_CHALLENGES
# Assuming DiscoveryChallengeURL is imported from eval.challenges
from collections import OrderedDict # For deterministic grouping based on first appearance of URL

_grouped_urls_data = OrderedDict()
for _challenge in JUICESHOP_DISCOVERY_CHALLENGES:
    if _challenge.url not in _grouped_urls_data:
        # For each new URL, store the id, key, and name of the first challenge encountered.
        # These will be used for the DiscoveryChallengeURL object.
        _grouped_urls_data[_challenge.url] = {
            "id": _challenge.id,
            "key": _challenge.key,
            "name": _challenge.name,
            "url_ids": []  # Initialize list to store all challenge IDs for this URL
        }
    _grouped_urls_data[_challenge.url]["url_ids"].append(_challenge.id)

JUICESHOP_DISCOVERY_URLS = [
    DiscoveryChallengeURL(
        id=data["id"],
        key=data["key"],
        name=data["name"], # Name from the first challenge associated with this URL
        url=url,
        url_ids=sorted(list(set(data["url_ids"]))) # List of unique, sorted challenge IDs for this URL
    )
    for url, data in _grouped_urls_data.items()
]

USERS = [
    {
        "username": "bjoern@juice-sh.op",
        "email": "bjoern@juice-sh.op",
        "role": "admin",
        "password": "monkey summer birthday are all bad passwords but work just fine in a long passphrase"
    },
    {
        "username": "john@juice-sh.op",
        "email": "john@juice-sh.op",
        "role": "customer",
        "password": "y&x5Z#f6W532Z4445#Ae2HkwZVyDb7&oCUaDzFU"
    },
    {
        "username": "jim@juice-sh.op",
        "email": "jim@juice-sh.op",
        "role": "customer",
        "password": "ncc-1701"
    }
]

def get_challenges(challenges):
    return [v for vuln in challenges.values() for v in vuln]