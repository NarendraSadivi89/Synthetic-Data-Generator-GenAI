-- Use an appropriate database; this line is optional and depends on your DBMS
-- CREATE DATABASE InsuranceDB;
-- USE InsuranceDB;

-- Customers Table
CREATE TABLE Customers (
    CustomerID INT PRIMARY KEY,
    FirstName VARCHAR(50),
    LastName VARCHAR(50),
    DateOfBirth DATE,
    Address VARCHAR(100),
    City VARCHAR(50),
    State VARCHAR(50),
    ZipCode VARCHAR(20)
);

-- PolicyTypes Table
CREATE TABLE PolicyTypes (
    PolicyTypeID INT PRIMARY KEY,
    PolicyTypeName VARCHAR(100),
    Description TEXT
);

-- Policies Table
CREATE TABLE Policies (
    PolicyID INT PRIMARY KEY,
    CustomerID INT,
    PolicyTypeID INT,
    StartDate DATE,
    EndDate DATE,
    Premium DECIMAL(10, 2),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    FOREIGN KEY (PolicyTypeID) REFERENCES PolicyTypes(PolicyTypeID)
);

-- Claims Table
CREATE TABLE Claims (
    ClaimID INT PRIMARY KEY,
    CustomerID INT,
    PolicyID INT,
    DateOfClaim DATE,
    ClaimAmount DECIMAL(10, 2),
    Status VARCHAR(30),
    FOREIGN KEY (PolicyID) REFERENCES Policies(PolicyID),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID)
);
