// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";

contract SafetyLog is AccessControl {
    bytes32 public constant GATEWAY_ROLE = keccak256("GATEWAY_ROLE");
    bytes32 public constant SAFETY_OPERATOR_ROLE = keccak256("SAFETY_OPERATOR_ROLE");

    enum Severity { WARNING, CRITICAL }
    enum Action { NONE, WARNING_TRIGGERED, EMERGENCY_STOP }

    struct Incident {
        bytes32 incidentId;
        bytes32 logHash;
        bytes32 cameraId;
        bytes32 robotId;
        bytes32 subjectId;
        Severity severity;
        Action action;
        uint256 recordedAt;
        address recordedBy;
    }

    mapping(bytes32 => Incident) public incidents;
    mapping(bytes32 => bool) public emergencyStopped;

    event IncidentRecorded(
        bytes32 indexed incidentId,
        bytes32 indexed robotId,
        bytes32 logHash,
        Severity severity,
        Action action,
        uint256 recordedAt,
        address recordedBy
    );

    event EmergencyStopRecorded(
        bytes32 indexed robotId,
        bytes32 indexed incidentId,
        uint256 recordedAt
    );

    event EmergencyStopCleared(bytes32 indexed robotId, uint256 clearedAt);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
    }

    function recordIncident(
        bytes32 incidentId,
        bytes32 logHash,
        bytes32 cameraId,
        bytes32 robotId,
        bytes32 subjectId,
        Severity severity,
        Action action
    ) external onlyRole(GATEWAY_ROLE) {
        require(incidents[incidentId].recordedAt == 0, "Incident already exists");

        incidents[incidentId] = Incident({
            incidentId: incidentId,
            logHash: logHash,
            cameraId: cameraId,
            robotId: robotId,
            subjectId: subjectId,
            severity: severity,
            action: action,
            recordedAt: block.timestamp,
            recordedBy: msg.sender
        });

        emit IncidentRecorded(
            incidentId,
            robotId,
            logHash,
            severity,
            action,
            block.timestamp,
            msg.sender
        );
    }

    function recordEmergencyStop(bytes32 robotId, bytes32 incidentId)
        external
        onlyRole(GATEWAY_ROLE)
    {
        emergencyStopped[robotId] = true;
        emit EmergencyStopRecorded(robotId, incidentId, block.timestamp);
    }

    function clearEmergencyStop(bytes32 robotId)
        external
        onlyRole(SAFETY_OPERATOR_ROLE)
    {
        emergencyStopped[robotId] = false;
        emit EmergencyStopCleared(robotId, block.timestamp);
    }

    function verifyLogHash(bytes32 incidentId, bytes32 calculatedHash)
        external
        view
        returns (bool)
    {
        return incidents[incidentId].logHash == calculatedHash;
    }
}
