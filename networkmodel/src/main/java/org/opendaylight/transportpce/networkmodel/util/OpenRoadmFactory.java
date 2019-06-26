/*
 * Copyright © 2019 AT&T and others.  All rights reserved.
 *
 * This program and the accompanying materials are made available under the
 * terms of the Eclipse Public License v1.0 which accompanies this distribution,
 * and is available at http://www.eclipse.org/legal/epl-v10.html
 */
package org.opendaylight.transportpce.networkmodel.util;

import org.opendaylight.transportpce.common.mapping.MappingUtils;
import org.opendaylight.transportpce.common.network.NetworkTransactionService;
import org.opendaylight.transportpce.networkmodel.dto.TopologyShard;
import org.opendaylight.yang.gen.v1.http.org.opendaylight.transportpce.portmapping.rev170228.network.Nodes;
import org.opendaylight.yang.gen.v1.urn.ietf.params.xml.ns.yang.ietf.network.topology.rev180226.networks.network.LinkBuilder;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OpenRoadmFactory {
    private static final Logger LOG = LoggerFactory.getLogger(OpenRoadmFactory.class);
    OpenRoadmTopology121 openRoadmTopology121;
    OpenRoadmTopology22 openRoadmTopology22;
    private final MappingUtils mappingUtils;

    public OpenRoadmFactory(MappingUtils mappingUtils, OpenRoadmTopology121 openRoadmTopology121,
                            OpenRoadmTopology22 openRoadmTopology22) {
        this.mappingUtils = mappingUtils;
        this.openRoadmTopology22 = openRoadmTopology22;
        this.openRoadmTopology121 = openRoadmTopology121;
    }

    public void createTopoLayerVersionControl(NetworkTransactionService networkTransactionService) {
        openRoadmTopology22.createTopoLayer();

    }

    public TopologyShard createTopologyShardVersionControl(Nodes mappingNode) {
        LOG.info("Create topology called for {} - version", mappingNode.getNodeId(),
            mappingNode.getOpenroadmVersion().getName());
        switch (mappingNode.getOpenroadmVersion().getName()) {
            case "1.2.1":
                return openRoadmTopology121.createTopologyShard(mappingNode.getNodeId());
            case "2.2.1":
                LOG.info("Creating openroadm topology v2.2 node for {}",mappingNode.getNodeId());
                return openRoadmTopology22.createTopologyShard(mappingNode);
            default:
                return null;

        }
    }

    public boolean deleteLink(String srcNode, String dstNode, String srcTp, String destTp,
                                                              NetworkTransactionService networkTransactionService) {

        return TopologyUtils.deleteLink(srcNode, dstNode, srcTp, destTp, networkTransactionService);
    }

    public LinkBuilder createLink(String srcNode, String dstNode, String srcTp, String destTp) {
        return TopologyUtils.createLink(srcNode,dstNode,srcTp,destTp);

    }
}
