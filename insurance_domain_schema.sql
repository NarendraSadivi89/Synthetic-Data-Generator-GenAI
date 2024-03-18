
        CREATE TABLE Customers (
            CustomerID INTEGER PRIMARY KEY,
            Name TEXT NOT NULL,
            Address TEXT,
            Phone TEXT,
            Email TEXT
        )
    ;


        CREATE TABLE Policies (
            PolicyID INTEGER PRIMARY KEY,
            CustomerID INTEGER,
            PolicyType TEXT,
            StartDate TEXT,
            EndDate TEXT,
            Premium REAL,
            FOREIGN KEY (CustomerID) REFERENCES Customers (CustomerID)
        )
    ;


        CREATE TABLE Claims (
            ClaimID INTEGER PRIMARY KEY,
            PolicyID INTEGER,
            DateOfClaim TEXT,
            ClaimAmount REAL,
            Status TEXT,
            FOREIGN KEY (PolicyID) REFERENCES Policies (PolicyID)
        )
    ;


        CREATE TABLE Agents (
            AgentID INTEGER PRIMARY KEY,
            Name TEXT,
            ContactInfo TEXT
        )
    ;


        CREATE TABLE PolicyAgent (
            PolicyID INTEGER,
            AgentID INTEGER,
            FOREIGN KEY (PolicyID) REFERENCES Policies (PolicyID),
            FOREIGN KEY (AgentID) REFERENCES Agents (AgentID)
        )
    ;


        CREATE TABLE Payments (
            PaymentID INTEGER PRIMARY KEY,
            PolicyID INTEGER,
            PaymentDate TEXT,
            Amount REAL,
            FOREIGN KEY (PolicyID) REFERENCES Policies (PolicyID)
        )
    ;


        CREATE TABLE VehicleInsurance (
            PolicyID INTEGER PRIMARY KEY,
            VehicleModel TEXT,
            VehicleYear INTEGER,
            VehicleID TEXT,
            FOREIGN KEY (PolicyID) REFERENCES Policies (PolicyID)
        )
    ;


        CREATE TABLE PropertyInsurance (
            PolicyID INTEGER PRIMARY KEY,
            PropertyAddress TEXT,
            PropertyType TEXT,
            PropertyValue REAL,
            FOREIGN KEY (PolicyID) REFERENCES Policies (PolicyID)
        )
    ;


        CREATE TABLE HealthInsurance (
            PolicyID INTEGER PRIMARY KEY,
            HealthCondition TEXT,
            CoverageAmount REAL,
            FOREIGN KEY (PolicyID) REFERENCES Policies (PolicyID)
        )
    ;


        CREATE TABLE LifeInsurance (
            PolicyID INTEGER PRIMARY KEY,
            BeneficiaryName TEXT,
            BeneficiaryRelationship TEXT,
            CoverageAmount REAL,
            FOREIGN KEY (PolicyID) REFERENCES Policies (PolicyID)
        )
    ;

