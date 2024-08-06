# Release Notes for Example Software v1.0.20240529.1

| Contents                                                                       | Details                                                        |
| ------------------------------------------------------------------------------ | -------------------------------------------------------------- |
| <li>[Summary](#summary)</li><li>[Epics](#epics)</li><li>[Others](#others)</li> | Version: v1.0.0<br>Issued: 2025-05-29<br>Software: Example<br> |

## Summary

In this iteration of Examine Plus, a series of enhancements and fixes were implemented to augment the application's effectiveness. Principal updates comprised advancements in the primary administration utilities for overseeing assessments and files, alongside the creation of a gateway permitting external parties to contribute proofs prior to assessments. The team rectified crucial defects concerning failure in initiation contacts and malfunctioning query Features within the assessments utility. Moreover, a script malfunction impacting the Automate feature was rectified, while enhancements in the automation workflows were realized through the incorporation of a Try Catch approach for the session invite workflow, boosting the overall system reliability.

<a id='epics'></a>

## <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_crown?color=E06C00&v=2' height='20' alt='Major Icon'> Epics

<div style='margin-left:1em'>

### <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_crown?color=E06C00&v=2' height='20' alt='Major Icon'> [#2007](https://dev.azure.com/EXAMPLE-ORG/2148e9b5-843c-4d32-a3de-5de1116cbd83/_apis/wit/workItems/2007) Examine+ Core

#### <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_trophy?color=773B93&v=2' height='17' alt='Function Icon'> Features

##### <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_trophy?color=773B93&v=2' height='17' alt='Function Icon'> [#11195](https://dev.azure.com/EXAMPLE-ORG/2148e9b5-843c-4d32-a3de-5de1116cbd83/_apis/wit/workItems/11195) Alerts & Error Management

- <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_insect?color=CC293D&v=2' height='17' alt='Defect Icon'> [#16181](https://dev.azure.com/EXAMPLE-ORG/2148e9b5-843c-4d32-a3de-5de1116cbd83/_apis/wit/workItems/16181) **Initiating Contact Invitations Unsuccessful** Resolved the defect causing unsuccessfulness in initiating contact invitations.

### <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_crown?color=E06C00&v=2' height='20' alt='Major Icon'> [#850](https://dev.azure.com/EXAMPLE-ORG/2148e9b5-843c-4d32-a3de-5de1116cbd83/_apis/wit/workItems/850) Examine+ Gateway

#### <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_trophy?color=773B93&v=2' height='17' alt='Function Icon'> Features

##### <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_trophy?color=773B93&v=2' height='17' alt='Function Icon'> [#1115](https://dev.azure.com/EXAMPLE-ORG/2148e9b5-843c-4d32-a3de-5de1116cbd83/_apis/wit/workItems/1115) Proof in Advance Gateway

- <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_insect?color=CC293D&v=2' height='17' alt='Defect Icon'> [#16338](https://dev.azure.com/EXAMPLE-ORG/2148e9b5-843c-4d32-a3de-5de1116cbd83/_apis/wit/workItems/16338) **Invitation Codes Malfunction** The complication with non-functional invitation codes has been corrected.

### <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_crown?color=E06C00&v=2' height='20' alt='Major Icon'> [#839](https://dev.azure.com/EXAMPLE-ORG/2148e9b5-843c-4d32-a3de-5de1116cbd83/_apis/wit/workItems/839) Examine+ Application

#### <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_trophy?color=773B93&v=2' height='17' alt='Function Icon'> Features

##### <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_trophy?color=773B93&v=2' height='17' alt='Function Icon'> [#1107](https://dev.azure.com/EXAMPLE-ORG/2148e9b5-843c-4d32-a3de-5de1116cbd83/_apis/wit/workItems/1107) Proof (App)

- <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_insect?color=CC293D&v=2' height='17' alt='Defect Icon'> [#17107](https://dev.azure.com/EXAMPLE-ORG/2148e9b5-843c-4d32-a3de-5de1116cbd83/_apis/wit/workItems/17107) **Query Function in Assessments Utility** Addressed.

</div>

<a id='others'></a>

## <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_review?color=333333&v=2' height='20' alt='Additional Icon'> Others

<div style='margin-left:1em'>

### <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_insect?color=CC293D&v=2' height='18' alt='Defect Icon'> Bugs

- <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_insect?color=CC293D&v=2' height='18' alt='Defect Icon'> [#17713](https://dev.azure.com/EXAMPLE-ORG/2148e9b5-843c-4d32-a3de-5de1116cbd83/_apis/wit/workItems/17713) **Script Malfunction** Addressed the script malfunction that caused a pop-up on the Account Interface when selecting an account in Automate Power.

### <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_list?color=009CCC&v=2' height='18' alt='Product Backlog Item Icon'> Product Backlog Items

- <img src='https://tfsproduks1.visualstudio.com/_apis/wit/workItemIcons/icon_list?color=009CCC&v=2' height='18' alt='Product Backlog Item Icon'> [#15981](https://dev.azure.com/EXAMPLE-ORG/2148e9b5-843c-4d32-a3de-5de1116cbd83/_apis/wit/workItems/15981) **Flow "Auto | Evidence | Dispatch Meeting Invitation" should incorporate Try Catch Approach and a condition trigger** Incorporated Try Catch Approach in the "Auto | Evidence | Dispatch Meeting Invitation" flow and established a trigger condition for the item type as described.

</div>
