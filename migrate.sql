-- Clean up old tables if they exist
DROP TABLE IF EXISTS user_info_old;
DROP TABLE IF EXISTS sell_ads_old;
DROP TABLE IF EXISTS buy_ads_old;

-- Migrate user_info
ALTER TABLE user_info RENAME TO user_info_old;

CREATE TABLE user_info (
    id INTEGER,
    userNo TEXT,
    registerDays INTEGER,
    firstOrderDays INTEGER,
    avgReleaseTimeOfLatest30day REAL,
    avgPayTimeOfLatest30day REAL,
    finishRateLatest30day REAL,
    completedOrderNumOfLatest30day INTEGER,
    completedBuyOrderNumOfLatest30day INTEGER,
    completedSellOrderNumOfLatest30day INTEGER,
    completedOrderNum INTEGER,
    completedBuyOrderNum INTEGER,
    completedSellOrderNum INTEGER,
    counterpartyCount INTEGER,
    userIdentity TEXT,
    badges TEXT,
    vipLevel INTEGER,
    lastActiveTime INTEGER,
    isCompanyAccount BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date DATE,
    PRIMARY KEY (userNo, date)
);

INSERT INTO user_info (id, userNo, registerDays, firstOrderDays, avgReleaseTimeOfLatest30day, avgPayTimeOfLatest30day, finishRateLatest30day, completedOrderNumOfLatest30day, completedBuyOrderNumOfLatest30day, completedSellOrderNumOfLatest30day, completedOrderNum, completedBuyOrderNum, completedSellOrderNum, counterpartyCount, userIdentity, badges, vipLevel, lastActiveTime, isCompanyAccount, created_at, date)
SELECT id, userNo, registerDays, firstOrderDays, avgReleaseTimeOfLatest30day, avgPayTimeOfLatest30day, finishRateLatest30day, completedOrderNumOfLatest30day, completedBuyOrderNumOfLatest30day, completedSellOrderNumOfLatest30day, completedOrderNum, completedBuyOrderNum, completedSellOrderNum, counterpartyCount, userIdentity, badges, vipLevel, lastActiveTime, isCompanyAccount, created_at, date(created_at) FROM user_info_old;

DROP TABLE user_info_old;

-- Migrate sell_ads
ALTER TABLE sell_ads RENAME TO sell_ads_old;

CREATE TABLE sell_ads (
    id INTEGER,
    userNo TEXT,
    advNo TEXT UNIQUE,
    tradeType TEXT,
    priceFloatingRatio TEXT,
    rateFloatingRatio TEXT,
    price TEXT,
    initAmount TEXT,
    surplusAmount TEXT,
    tradableQuantity TEXT,
    amountAfterEditing TEXT,
    maxSingleTransAmount TEXT,
    minSingleTransAmount TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date DATE,
    PRIMARY KEY (userNo, date),
    FOREIGN KEY (userNo) REFERENCES user_info(userNo)
);

INSERT INTO sell_ads (id, userNo, advNo, tradeType, priceFloatingRatio, rateFloatingRatio, price, initAmount, surplusAmount, tradableQuantity, amountAfterEditing, maxSingleTransAmount, minSingleTransAmount, created_at, date)
SELECT id, userNo, advNo, tradeType, priceFloatingRatio, rateFloatingRatio, price, initAmount, surplusAmount, tradableQuantity, amountAfterEditing, maxSingleTransAmount, minSingleTransAmount, created_at, date(created_at) FROM sell_ads_old;

DROP TABLE sell_ads_old;

-- Migrate buy_ads
ALTER TABLE buy_ads RENAME TO buy_ads_old;

CREATE TABLE buy_ads (
    id INTEGER,
    userNo TEXT,
    advNo TEXT UNIQUE,
    tradeType TEXT,
    priceFloatingRatio TEXT,
    rateFloatingRatio TEXT,
    price TEXT,
    initAmount TEXT,
    surplusAmount TEXT,
    tradableQuantity TEXT,
    amountAfterEditing TEXT,
    maxSingleTransAmount TEXT,
    minSingleTransAmount TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date DATE,
    PRIMARY KEY (userNo, date),
    FOREIGN KEY (userNo) REFERENCES user_info(userNo)
);

INSERT INTO buy_ads (id, userNo, advNo, tradeType, priceFloatingRatio, rateFloatingRatio, price, initAmount, surplusAmount, tradableQuantity, amountAfterEditing, maxSingleTransAmount, minSingleTransAmount, created_at, date)
SELECT id, userNo, advNo, tradeType, priceFloatingRatio, rateFloatingRatio, price, initAmount, surplusAmount, tradableQuantity, amountAfterEditing, maxSingleTransAmount, minSingleTransAmount, created_at, date(created_at) FROM buy_ads_old;

DROP TABLE buy_ads_old;
