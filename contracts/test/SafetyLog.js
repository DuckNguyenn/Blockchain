const { expect } = require("chai");

describe("SafetyLog", function () {
  async function deployed() {
    const [admin, gateway, operator, stranger] = await ethers.getSigners();
    const Factory = await ethers.getContractFactory("SafetyLog");
    const contract = await Factory.deploy(admin.address);
    await contract.waitForDeployment();
    await contract.grantRole(await contract.GATEWAY_ROLE(), gateway.address);
    await contract.grantRole(
      await contract.SAFETY_OPERATOR_ROLE(),
      operator.address
    );
    return { contract, admin, gateway, operator, stranger };
  }

  it("records an incident only from the gateway", async function () {
    const { contract, gateway, stranger } = await deployed();
    const incidentId = ethers.encodeBytes32String("INC-001");
    const logHash = ethers.keccak256(ethers.toUtf8Bytes("incident"));
    const cameraId = ethers.encodeBytes32String("CAM-001");
    const robotId = ethers.encodeBytes32String("ROBOT-001");
    const subjectId = ethers.encodeBytes32String("TRACK-001");

    await expect(
      contract.connect(stranger).recordIncident(
        incidentId,
        logHash,
        cameraId,
        robotId,
        subjectId,
        1,
        2
      )
    ).to.be.reverted;

    await expect(
      contract.connect(gateway).recordIncident(
        incidentId,
        logHash,
        cameraId,
        robotId,
        subjectId,
        1,
        2
      )
    ).to.emit(contract, "IncidentRecorded");

    expect(await contract.verifyLogHash(incidentId, logHash)).to.equal(true);
  });

  it("allows only the safety operator to clear emergency stop", async function () {
    const { contract, gateway, operator, stranger } = await deployed();
    const robotId = ethers.encodeBytes32String("ROBOT-001");
    const incidentId = ethers.encodeBytes32String("INC-001");

    await contract.connect(gateway).recordEmergencyStop(robotId, incidentId);
    expect(await contract.emergencyStopped(robotId)).to.equal(true);
    await expect(contract.connect(stranger).clearEmergencyStop(robotId)).to.be.reverted;
    await contract.connect(operator).clearEmergencyStop(robotId);
    expect(await contract.emergencyStopped(robotId)).to.equal(false);
  });
});
